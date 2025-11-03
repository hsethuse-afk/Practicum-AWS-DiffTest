from .contracts import RunConfig, TargetPair, LoggerMode
from .diffpairer import DiffPairer
from .strategy.strategies import StrategySynthesizer
from .strategy.strategy_serializer import StrategySerializer
from .type_inference.type_discovery import TypeDiscoverer
from .type_inference.type_inference_engine import TypeInferenceEngine
from .type_inference.righttyper_engine import RightTyperEngine
from .harness import HarnessBuilder
from .abrunner import ABRunner
from .results import ResultCollector
from .logger import Logger
from .comparator import ABComparator
from .project_builder import ProjectBuilder
from . import logger


class Orchestrator:
    def __init__(
        self,
        log_mode: LoggerMode = LoggerMode.Normal,
        inference_engine: TypeInferenceEngine = None,
        enable_strategy_extras: list = None,
    ):
        """
        Initialize the orchestrator.

        Args:
            log_mode: Logging verbosity level
            inference_engine: Type inference engine to use (default: RightTyperEngine)
                             Can be swapped for other engines (MonkeyType, Pytype, etc.)
            enable_strategy_extras: List of extra Hypothesis strategy modules to enable
                                   (e.g., ['numpy', 'pandas']). If None, enables all available.
        """
        logger.set_logger(Logger(log_mode))
        self.log = logger.get_logger()
        self.harness = HarnessBuilder()
        self.type_discoverer = TypeDiscoverer()
        self.inference_engine = inference_engine or RightTyperEngine()
        self.strategy = StrategySynthesizer()
        self.serializer = StrategySerializer(enable_extras=enable_strategy_extras)
        self.runner = ABRunner()
        self.comparator = ABComparator()
        self.results = ResultCollector()
        self.project_builder = ProjectBuilder()

    def run_pair(
        self,
        file_a: str,
        file_b: str,
        func_name: str,
        max_examples: int = 200,
        test_file: str = None,
        auto_approve: bool = False,
    ):
        """
        Run differential testing on a pair of functions.

        Args:
            file_a: Path to first file
            file_b: Path to second file
            func_name: Name of the function to test
            max_examples: Maximum number of test examples
            test_file: Optional path to test file for RightTyper type inference
                      (e.g., "test.py") that will be used if annotations are missing
            strategy_file: Optional path to save/load strategy JSON file
                          If provided, will save strategy and wait for user confirmation
            auto_approve: If True, skip user confirmation and use saved strategy immediately
        """

        # TODO if strategy file exits, skip the type inference

        # Step 1: Validate test file
        if test_file:
            import os

            if not os.path.exists(test_file):
                self.log.debug(
                    f"[Orchestrator] Test file not found: {test_file}"
                )
                test_file = None
            else:
                self.log.verbose(
                    f"[Orchestrator] Using test file for type inference: {test_file}"
                )

        # Step 2: Build target pairs (load functions from files)
        target = TargetPair(
            file_a=file_a, file_b=file_b, func_name=func_name
        )
        fn_a, fn_b = self.harness.build(target)

        # Step 3: Run type inference if needed
        if test_file and self.inference_engine.needs_inference(
            fn_a, test_file
        ):
            self.log.verbose(
                f"[Orchestrator] Running {self.inference_engine.get_engine_name()} to infer types"
            )
            success = self.inference_engine.run_inference(test_file)
            if success:
                self.log.verbose(
                    f"[Orchestrator] Type inference completed, reloading functions"
                )
                # Reload functions via harness to get updated annotations
                fn_a, fn_b = self.harness.build(target)

        # Step 4: Discover parameter types from (possibly updated) function
        param_types = self.type_discoverer.discover_param_types(fn_a)
        self.log.verbose(
            f"[Orchestrator] Discovered types: {param_types}"
        )

        # Step 5: Generate new strategy from discovered types
        plan = self.strategy.create_strategy(
            fn_a, param_types=param_types
        )
        self.log.verbose(
            f"✅ Test Strategies Successfully Generated:\n{plan}"
        )

        # Step 6: Save strategy and wait for user confirmation if requested
        if not auto_approve:
            strategy_file = f"strategy_{func_name}.json"
            self.serializer.save_to_file(plan, strategy_file, fn_a)

            # Print formatted configuration to console
            self.log.verbose(
                f"[Orchestrator] Strategy saved to: {strategy_file}"
            )

            # Wait for user input
            print(f"Configuration saved to: {strategy_file}")
            print("\nReview the configuration above. You can:")
            print("  - Press Enter to continue with this configuration")
            print(
                "  - Edit the JSON file to modify parameters and press Enter to reload"
            )
            print("  - Press Ctrl+C to cancel")

            import os
            import inspect

            # Get function's module globals for user-defined types
            fn_globals = {}
            try:
                fn_module = inspect.getmodule(fn_a)
                if fn_module:
                    fn_globals = vars(fn_module)
            except Exception:
                pass

            try:
                input("\nPress Enter to continue...")

                # Reload configuration from file (in case user edited it)
                if os.path.exists(strategy_file):
                    print("\nReloading configuration from file...")
                    plan = self.serializer.load_from_file(
                        strategy_file, fn_globals
                    )
                    print("✅ Configuration loaded successfully")
                else:
                    print(
                        f"\n⚠️ Warning: Configuration file {strategy_file} not found. Using original configuration.\n"
                    )
            except KeyboardInterrupt:
                print("\n\n❌ Testing cancelled by user.")
                return None

            self.log.verbose(f"✅ Test Strategies Loaded:\n{plan}")

        # Run and Compare
        a_results, b_results, warnings = self.runner.execute(
            fn_a, fn_b, plan, RunConfig(max_examples=max_examples)
        )
        cmp = self.comparator.compare(a_results, b_results)
        out = self.results.collect(target, cmp, warnings)
        self.results.print(out)

        return out

    def run_git_diff(
        self,
        commit: str = "HEAD",
        func_name: str = None,
        max_examples: int = 200,
        test_file: str = None,
        strategy_file: str = None,
        auto_approve: bool = False,
    ):
        """
        Run differential testing on modified functions from a git commit.

        Args:
            commit: Git commit reference (e.g., "HEAD", "abc123", "HEAD~1")
            func_name: Optional filter for specific function name
            max_examples: Maximum number of test examples per function
            test_file: Optional path to test file for type inference
            strategy_file: Optional path to save/load strategy JSON file
            auto_approve: If True, skip user confirmation for strategies

        Returns:
            List of test results for each modified function
        """
        from .diffpairer import DiffPairer

        pairer = DiffPairer()

        # Get modified functions from git diff
        self.log.verbose(f"[Orchestrator] Parsing git commit: {commit}")
        pairs = pairer.pair_from_git_commit(commit, func_name)

        if not pairs:
            self.log.verbose(
                "[Orchestrator] No modified functions found"
            )
            return []

        self.log.verbose(
            f"[Orchestrator] Found {len(pairs)} modified function(s)"
        )

        # Run tests on each pair
        results = []
        for i, (target, cleanup) in enumerate(pairs, 1):
            self.log.verbose(
                f"[Orchestrator] Testing {i}/{len(pairs)}: {target.func_name}"
            )

            try:
                # Generate strategy file name for each function if base path provided
                func_strategy_file = None
                if strategy_file:
                    func_strategy_file = strategy_file.replace(
                        ".json", f"_{target.func_name}.json"
                    )

                result = self.run_pair(
                    file_a=target.file_a,
                    file_b=target.file_b,
                    func_name=target.func_name,
                    max_examples=max_examples,
                    test_file=test_file,
                    strategy_file=func_strategy_file,
                    auto_approve=auto_approve,
                )
                results.append(result)
            finally:
                cleanup()

        return results

    def run_diff_file(
        self,
        diff_file_path: str,
        func_name: str = None,
        max_examples: int = 200,
        test_file: str = None,
        strategy_file: str = None,
        auto_approve: bool = False,
    ):
        """
        Run differential testing on modified functions from a diff file.

        Args:
            diff_file_path: Path to file containing git diff
            func_name: Optional filter for specific function name
            max_examples: Maximum number of test examples per function
            test_file: Optional path to test file for type inference
            strategy_file: Optional path to save/load strategy JSON file
            auto_approve: If True, skip user confirmation for strategies

        Returns:
            List of test results for each modified function
        """
        from .diffpairer import DiffPairer

        pairer = DiffPairer()

        # Get modified functions from diff file
        self.log.verbose(
            f"[Orchestrator] Parsing diff file: {diff_file_path}"
        )
        pairs = pairer.pair_from_diff_file(diff_file_path, func_name)

        if not pairs:
            self.log.verbose(
                "[Orchestrator] No modified functions found"
            )
            return []

        self.log.verbose(
            f"[Orchestrator] Found {len(pairs)} modified function(s)"
        )

        # Run tests on each pair
        results = []
        for i, (target, cleanup) in enumerate(pairs, 1):
            self.log.verbose(
                f"[Orchestrator] Testing {i}/{len(pairs)}: {target.func_name}"
            )

            try:
                # Generate strategy file name for each function if base path provided
                func_strategy_file = None
                if strategy_file:
                    func_strategy_file = strategy_file.replace(
                        ".json", f"_{target.func_name}.json"
                    )

                result = self.run_pair(
                    file_a=target.file_a,
                    file_b=target.file_b,
                    func_name=target.func_name,
                    max_examples=max_examples,
                    test_file=test_file,
                    strategy_file=func_strategy_file,
                    auto_approve=auto_approve,
                )
                results.append(result)
            finally:
                cleanup()

        return results

    def run_diff_with_repo(
        self,
        diff_file_path: str,
        repo_url: str,
        commit: str = None,
        func_name: str = None,
        max_examples: int = 200,
        install_deps: bool = True,
        strategy_file: str = None,
        auto_approve: bool = False,
    ):
        """
        Run differential testing from a diff file with repository context.

        This is the key method for testing when you only have a git diff.
        It will:
        1. Clone the repository
        2. Install dependencies
        3. Parse the diff to find modified functions
        4. Run differential tests with full type inference support

        Args:
            diff_file_path: Path to file containing git diff
            repo_url: Repository URL to clone (e.g., "https://github.com/user/repo.git")
            commit: Optional specific commit (extracted from diff if not provided)
            func_name: Optional filter for specific function name
            max_examples: Maximum number of test examples per function
            install_deps: Whether to install dependencies from requirements.txt
            strategy_file: Optional path to save/load strategy JSON file
            auto_approve: If True, skip user confirmation for strategies

        Returns:
            List of test results for each modified function
        """
        import os

        # Read diff file
        with open(diff_file_path, "r") as f:
            diff_content = f.read()

        # Build project environment
        self.log.verbose(
            f"[Orchestrator] Building project from {repo_url}"
        )
        if install_deps:
            env = self.project_builder.build_from_url(
                repo_url, commit or "HEAD", install_deps=True
            )
        else:
            env = self.project_builder.build_from_diff_with_repo(
                diff_content, repo_url, commit
            )

        try:
            self.log.verbose(
                f"[Orchestrator] Project cloned to: {env.project_root}"
            )

            # Find test file if exists (for type inference)
            test_file = self._find_test_file(env.project_root)

            # Parse diff to find modified functions
            pairer = DiffPairer()
            self.log.verbose(
                f"[Orchestrator] Parsing diff file: {diff_file_path}"
            )

            # Change to project root for relative paths to work
            original_cwd = os.getcwd()
            os.chdir(env.project_root)

            try:
                # Get pairs for testing and extract info about all modified functions
                pairs = pairer.pair_from_diff_file(
                    diff_file_path, func_name, commit
                )

                # Also get ALL modified functions (including class methods) for reporting
                all_modified = pairer.git_parser.parse_diff_from_file(
                    diff_file_path, commit
                )

                # Report all found functions/methods
                if all_modified:
                    module_funcs = [
                        m for m in all_modified if not m.is_class_method
                    ]
                    class_methods = [
                        m for m in all_modified if m.is_class_method
                    ]

                    print(
                        f"\n📋 Found {len(all_modified)} modified function(s)/method(s):"
                    )

                    if module_funcs:
                        print(
                            f"\n✅ Module-level functions (can test): {len(module_funcs)}"
                        )
                        for m in module_funcs:
                            print(
                                f"   - {m.function_name}() at lines {m.line_start}-{m.line_end}"
                            )

                    if class_methods:
                        print(
                            f"\n📦 Class methods (extracted but not tested yet): {len(class_methods)}"
                        )
                        for m in class_methods:
                            print(
                                f"   - {m.class_name}.{m.function_name}() at lines {m.line_start}-{m.line_end}"
                            )
                    print()

                if not pairs:
                    self.log.verbose(
                        "[Orchestrator] No testable functions found (class methods are not supported yet)"
                    )
                    return []

                self.log.verbose(
                    f"[Orchestrator] Testing {len(pairs)} module-level function(s)"
                )

                # Update harness with venv_path if available
                if env.venv_path:
                    self.log.verbose(
                        f"[Orchestrator] Using virtual environment: {env.venv_path}"
                    )
                    self.harness = HarnessBuilder(
                        venv_path=env.venv_path
                    )

                # Run tests on each pair
                results = []
                for i, (target, cleanup_pair) in enumerate(pairs, 1):
                    self.log.verbose(
                        f"[Orchestrator] Testing {i}/{len(pairs)}: {target.func_name}"
                    )

                    try:
                        # Generate strategy file name for each function if base path provided
                        func_strategy_file = None
                        if strategy_file:
                            func_strategy_file = strategy_file.replace(
                                ".json", f"_{target.func_name}.json"
                            )

                        result = self.run_pair(
                            file_a=target.file_a,
                            file_b=target.file_b,
                            func_name=target.func_name,
                            max_examples=max_examples,
                            test_file=test_file,
                            strategy_file=func_strategy_file,
                            auto_approve=auto_approve,
                        )
                        results.append(result)
                    finally:
                        cleanup_pair()

                return results
            finally:
                os.chdir(original_cwd)

        finally:
            env.cleanup()

    def _find_test_file(self, project_root: str) -> str:
        """
        Try to find a test file for type inference.

        Args:
            project_root: Root directory of the project

        Returns:
            Path to test file if found, None otherwise
        """
        import os
        import glob

        # Common test file patterns
        patterns = [
            "test_*.py",
            "*_test.py",
            "tests/test_*.py",
            "tests/*_test.py",
        ]

        for pattern in patterns:
            matches = glob.glob(
                os.path.join(project_root, "**", pattern),
                recursive=True,
            )
            if matches:
                self.log.verbose(
                    f"[Orchestrator] Found test file: {matches[0]}"
                )
                return matches[0]

        self.log.verbose("[Orchestrator] No test file found")
        return None
