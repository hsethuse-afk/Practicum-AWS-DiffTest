import os
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
        timeout: int = None,
    ):
        """
        Initialize the orchestrator.

        Args:
            log_mode: Logging verbosity level
            inference_engine: Type inference engine to use (default: RightTyperEngine)
                             Can be swapped for other engines (MonkeyType, Pytype, etc.)
            enable_strategy_extras: List of extra Hypothesis strategy modules to enable
                                   (e.g., ['numpy', 'pandas']). If None, enables all available.
            timeout: Optional timeout in seconds for run_pair execution (default: None, no timeout)
        """
        logger.set_logger(Logger(log_mode))
        self.log = logger.get_logger()
        self.harness = HarnessBuilder()
        self.type_discoverer = TypeDiscoverer()
        self.inference_engine = inference_engine or RightTyperEngine()
        self.strategy = StrategySynthesizer()
        self.serializer = StrategySerializer(
            enable_extras=enable_strategy_extras
        )
        self.runner = ABRunner(timeout=timeout)
        self.comparator = ABComparator()
        self.results = ResultCollector()
        self.project_builder = ProjectBuilder()
        self.timeout = timeout

        self.difference = True

    def run_pair(
        self,
        file_a: str,
        file_b: str,
        func_name: str,
        max_examples: int = 200,
        test_file: str = None,
        auto_approve: bool = False,
        report_path: str = None,
        seed: int = None,
        timeout: int = None,
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
            auto_approve: If True, skip user confirmation and use saved strategy immediately
            report_path: Optional path to save HTML report
            seed: Optional random seed for reproducible test generation
            timeout: Optional timeout in seconds for test execution (overrides instance timeout)
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

        # Step 2: Build target pairs (load functions or class methods from files)
        target = TargetPair(
            file_a=file_a, file_b=file_b, func_name=func_name
        )
        result_a, result_b = self.harness.build(target)

        # Check if we're testing class methods or regular functions
        is_class_method = (
            isinstance(result_a, tuple) and len(result_a) == 2
        )

        if is_class_method:
            cls_a, fn_a = result_a
            cls_b, fn_b = result_b
            self.log.verbose(
                f"[Orchestrator] Testing class method: {cls_a.__name__}.{func_name}"
            )
        else:
            fn_a, fn_b = result_a, result_b
            cls_a, cls_b = None, None
            self.log.verbose(
                f"[Orchestrator] Testing function: {func_name}"
            )

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
                # Reload functions/methods via harness to get updated annotations
                result_a, result_b = self.harness.build(target)
                if is_class_method:
                    cls_a, fn_a = result_a
                    cls_b, fn_b = result_b
                else:
                    fn_a, fn_b = result_a, result_b

        # Step 4: Discover parameter types from (possibly updated) function
        param_types = self.type_discoverer.discover_param_types(fn_a)
        self.log.verbose(
            f"[Orchestrator] Discovered method/function parameter types: {param_types}"
        )

        # Step 4b: For class methods, discover constructor types
        constructor_types = None
        if is_class_method:
            constructor_types = (
                self.type_discoverer.discover_constructor_types(cls_a)
            )
            self.log.verbose(
                f"[Orchestrator] Discovered constructor types for {cls_a.__name__}: {constructor_types}"
            )

        # Step 5: Generate new strategy from discovered types
        plan = self.strategy.create_strategy(
            fn_a,
            param_types=param_types,
            cls=cls_a,
            constructor_types=constructor_types,
            max_examples=max_examples,
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
        import time
        import random

        start_time = time.time()

        # Generate seed if not provided
        if seed is None:
            seed = random.randint(0, 2**32 - 1)
            self.log.verbose(f"\n🎲 Generated random seed: {seed}")
        else:
            self.log.verbose(f"\n🎲 Using provided seed: {seed}")

        run_config = RunConfig(max_examples=max_examples, seed=seed)

        # Use provided timeout or fall back to instance timeout
        effective_timeout = (
            timeout if timeout is not None else self.timeout
        )

        a_results, b_results, warnings = self.runner.execute(
            fn_a, fn_b, plan, run_config, timeout=effective_timeout
        )

        duration = time.time() - start_time

        # If timeout occurred and no results, return None
        if effective_timeout and not a_results and not b_results:
            self.log.normal(
                f"\n⏱️  Test timed out after {effective_timeout}s with no results"
            )
            return None

        cmp = self.comparator.compare(a_results, b_results)
        out = self.results.collect(target, cmp, warnings)
        self.results.print(out)

        # Generate HTML report if requested
        if report_path:
            self._generate_html_report(
                test_result=out,
                a_results=a_results,
                b_results=b_results,
                strategy=plan,
                config=run_config,
                command=self._build_command_string(
                    file_a, file_b, func_name, max_examples, seed
                ),
                duration=duration,
                output_path=report_path,
            )

        return out

    def get_difference(self, result):
        """
        Get a simple summary of the test result.

        Args:
            result: TestResult object from run_pair

        Returns:
            Dictionary with difference_found, total_examples, mismatches, reason
        """
        return self.results.get_difference(result)

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

    def run_patch_file(
        self,
        patch_file_path: str,
        func_name: str = None,
        max_examples: int = 200,
        auto_approve: bool = False,
        report_path: str = None,
        seed: int = None,
    ):
        """
        Run differential testing on modified functions from a patch file.
        This mode doesn't require git commit context - it reconstructs
        the old and new versions directly from the patch.

        Args:
            patch_file_path: Path to file containing git diff/patch
            func_name: Optional filter for specific function name
            max_examples: Maximum number of test examples per function
            auto_approve: If True, skip user confirmation for strategies
            report_path: Optional path to save HTML report
            seed: Optional random seed for reproducible test generation

        Returns:
            List of test results for each modified function
        """
        from .diffpairer import DiffPairer

        pairer = DiffPairer()

        # Get modified functions from patch file
        self.log.verbose(
            f"[Orchestrator] Parsing patch file: {patch_file_path}"
        )
        pairs = pairer.pair_from_patch(patch_file_path, func_name)

        if not pairs:
            self.log.verbose(
                "[Orchestrator] No modified functions found in patch"
            )
            return []

        self.log.verbose(
            f"[Orchestrator] Found {len(pairs)} modified function(s) in patch"
        )

        # Run tests on each pair
        results = []
        for i, (target, cleanup) in enumerate(pairs, 1):
            self.log.verbose(
                f"[Orchestrator] Testing {i}/{len(pairs)}: {target.func_name}"
            )

            # Generate unique report path for each function if report_path is provided
            func_report_path = None
            if report_path:
                if len(pairs) > 1:
                    # Multiple functions: add function name to report path
                    import os as os_module

                    base, ext = os_module.path.splitext(report_path)
                    func_report_path = f"{base}_{target.func_name}{ext}"
                else:
                    # Single function: use original report path
                    func_report_path = report_path

            try:
                result = self.run_pair(
                    file_a=target.file_a,
                    file_b=target.file_b,
                    func_name=target.func_name,
                    max_examples=max_examples,
                    auto_approve=auto_approve,
                    report_path=func_report_path,
                    seed=seed,
                )
                results.append(result)
            finally:
                cleanup()

        return results

    def run_patch_from_repo(
        self,
        repo_url: str,
        patch_file_path: str,
        func_name: str = None,
        max_examples: int = 200,
        install_deps: bool = True,
        auto_approve: bool = False,
        interactive_select: bool = True,
        selected_functions: str = None,
        report_path: str = None,
        seed: int = None,
    ):
        """
        Run differential testing from a patch file + repository URL.

        This mode clones the repository and applies the patch to reconstruct
        old and new versions of the modified functions.

        Args:
            repo_url: Repository URL to clone (e.g., "https://github.com/user/repo.git")
            patch_file_path: Path to patch/diff file
            func_name: Optional filter for specific function name
            max_examples: Maximum number of test examples per function
            install_deps: Whether to install dependencies from requirements.txt
            auto_approve: If True, skip user confirmation for strategies
            interactive_select: If True, prompt user to select functions interactively
            selected_functions: Pre-selected function indices (e.g., "1,2,3" or "1-3")
            report_path: Optional path to save HTML report
            seed: Optional random seed for reproducible test generation

        Returns:
            List of test results for each modified function
        """
        import os
        import subprocess

        # Build project environment (clone repo without checking out specific commit)
        self.log.verbose(
            f"[Orchestrator] Cloning repository from {repo_url}"
        )
        # For patch mode, we don't have a commit, so we'll use HEAD or master
        env = self.project_builder.build_from_url(
            repo_url, commit="HEAD", install_deps=install_deps
        )

        try:
            self.log.verbose(
                f"[Orchestrator] Project cloned to: {env.project_root}"
            )

            # Find test file if exists (for type inference)
            test_file = self._find_test_file(env.project_root)

            # Change to project root to read files referenced in patch
            original_cwd = os.getcwd()
            os.chdir(env.project_root)

            try:
                # Parse patch to find modified functions
                from .diffpairer import DiffPairer

                pairer = DiffPairer()

                self.log.verbose(
                    f"[Orchestrator] Parsing patch file: {patch_file_path}"
                )

                # Use the patch parser which will read files from the cloned repo
                pairs = pairer.pair_from_patch(
                    os.path.join(original_cwd, patch_file_path),
                    func_name,
                )

                if not pairs:
                    self.log.verbose(
                        "[Orchestrator] No modified functions found in patch"
                    )
                    return []

                # Let user select which functions to test
                selected_pairs = self._select_functions_to_test(
                    pairs,
                    interactive=interactive_select,
                    preselected=selected_functions,
                )

                if not selected_pairs:
                    print("\n❌ No functions selected for testing.")
                    return []

                self.log.verbose(
                    f"[Orchestrator] Testing {len(selected_pairs)} selected function(s)"
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
                for i, (target, cleanup_pair) in enumerate(
                    selected_pairs, 1
                ):
                    self.log.verbose(
                        f"[Orchestrator] Testing {i}/{len(selected_pairs)}: {target.func_name}"
                    )

                    # Generate unique report path for each function if report_path is provided
                    func_report_path = None
                    if report_path:
                        if len(selected_pairs) > 1:
                            # Multiple functions: add function name to report path
                            import os as os_module

                            base, ext = os_module.path.splitext(
                                report_path
                            )
                            func_report_path = (
                                f"{base}_{target.func_name}{ext}"
                            )
                        else:
                            # Single function: use original report path
                            func_report_path = report_path

                    try:
                        result = self.run_pair(
                            file_a=target.file_a,
                            file_b=target.file_b,
                            func_name=target.func_name,
                            max_examples=max_examples,
                            test_file=test_file,
                            auto_approve=auto_approve,
                            report_path=func_report_path,
                            seed=seed,
                        )
                        results.append(result)
                    finally:
                        cleanup_pair()

                return results
            finally:
                os.chdir(original_cwd)

        finally:
            env.cleanup()

    def run_commit_from_repo(
        self,
        repo_url: str,
        commit: str,
        func_name: str = None,
        max_examples: int = 200,
        install_deps: bool = True,
        auto_approve: bool = False,
        interactive_select: bool = True,
        selected_functions: str = None,
        report_path: str = None,
        seed: int = None,
    ):
        """
        Run differential testing directly from a commit in a remote repository.

        This is simpler than run_diff_with_repo - just provide repo URL and commit!
        It will:
        1. Clone the repository
        2. Install dependencies
        3. Extract diff from the commit
        4. Parse the diff to find modified functions
        5. Run differential tests with full type inference support

        Args:
            repo_url: Repository URL to clone (e.g., "https://github.com/user/repo.git")
            commit: Commit hash to test (e.g., "ed7facc1b108ceff12bcb412d7a98471509f41b0")
            func_name: Optional filter for specific function name
            max_examples: Maximum number of test examples per function
            install_deps: Whether to install dependencies from requirements.txt
            auto_approve: If True, skip user confirmation for strategies
            interactive_select: If True, prompt user to select functions interactively
            selected_functions: Pre-selected function indices (e.g., "1,2,3" or "1-3")
            report_path: Optional path to save HTML report
            seed: Optional random seed for reproducible test generation

        Returns:
            List of test results for each modified function
        """
        import os
        import subprocess

        # Build project environment
        self.log.verbose(
            f"[Orchestrator] Building project from {repo_url}"
        )
        env = self.project_builder.build_from_url(
            repo_url, commit, install_deps=install_deps
        )

        try:
            self.log.verbose(
                f"[Orchestrator] Project cloned to: {env.project_root}"
            )

            # Find test file if exists (for type inference)
            test_file = self._find_test_file(env.project_root)

            # Change to project root for git commands
            original_cwd = os.getcwd()
            os.chdir(env.project_root)

            try:
                # Get diff from commit
                self.log.verbose(
                    f"[Orchestrator] Extracting diff from commit: {commit}"
                )
                cmd = ["git", "diff", f"{commit}^", commit]
                result = subprocess.run(
                    cmd, capture_output=True, text=True, check=True
                )
                diff_content = result.stdout

                # Save diff to temporary file for parsing
                import tempfile

                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".diff", delete=False
                ) as tmp:
                    tmp.write(diff_content)
                    tmp_diff_path = tmp.name

                try:
                    # Parse diff to find modified functions
                    pairer = DiffPairer()
                    self.log.verbose(
                        f"[Orchestrator] Parsing diff from commit"
                    )

                    # Get pairs for testing and extract info about all modified functions
                    pairs = pairer.pair_from_diff_file(
                        tmp_diff_path,
                        func_name,
                        commit,
                        project_root=env.project_root,
                    )

                    # Also get ALL modified functions (including class methods) for reporting
                    all_modified = (
                        pairer.git_parser.parse_diff_from_file(
                            tmp_diff_path, commit
                        )
                    )

                    # Report all found functions/methods
                    if all_modified:
                        module_funcs = [
                            m
                            for m in all_modified
                            if not m.is_class_method
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
                            for i, m in enumerate(module_funcs, 1):
                                print(
                                    f"   {i}. {m.function_name}() at lines {m.line_start}-{m.line_end}"
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
                finally:
                    # Clean up temp diff file
                    os.unlink(tmp_diff_path)

                # Let user select which functions to test
                selected_pairs = self._select_functions_to_test(
                    pairs,
                    interactive=interactive_select,
                    preselected=selected_functions,
                )

                if not selected_pairs:
                    print("\n❌ No functions selected for testing.")
                    return []

                self.log.verbose(
                    f"[Orchestrator] Testing {len(selected_pairs)} selected function(s)"
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
                for i, (target, cleanup_pair) in enumerate(
                    selected_pairs, 1
                ):
                    self.log.verbose(
                        f"[Orchestrator] Testing {i}/{len(selected_pairs)}: {target.func_name}"
                    )

                    # Generate unique report path for each function if report_path is provided
                    func_report_path = None
                    if report_path:
                        if len(selected_pairs) > 1:
                            # Multiple functions: add function name to report path
                            import os as os_module

                            base, ext = os_module.path.splitext(
                                report_path
                            )
                            func_report_path = (
                                f"{base}_{target.func_name}{ext}"
                            )
                        else:
                            # Single function: use original report path
                            func_report_path = report_path

                    try:
                        result = self.run_pair(
                            file_a=target.file_a,
                            file_b=target.file_b,
                            func_name=target.func_name,
                            max_examples=max_examples,
                            test_file=test_file,
                            auto_approve=auto_approve,
                            report_path=func_report_path,
                            seed=seed,
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

    def _select_functions_to_test(
        self,
        pairs: list,
        interactive: bool = True,
        preselected: str = None,
    ) -> list:
        """
        Let user select which functions to test.

        Args:
            pairs: List of (TargetPair, cleanup_function) tuples
            interactive: If True, prompt user for selection; otherwise use preselected or all
            preselected: Pre-selected function indices (e.g., "1,2,3" or "1-3")

        Returns:
            List of selected (TargetPair, cleanup_function) tuples
        """
        if not pairs:
            return []

        # Non-interactive mode with preselected functions
        if not interactive and preselected:
            selected_indices = self._parse_function_selection(
                preselected, len(pairs)
            )
            if selected_indices is None:
                print(
                    "⚠️  Invalid function selection. Testing all functions."
                )
                return pairs

            selected_pairs = [
                pairs[idx - 1] for idx in selected_indices
            ]
            print(f"\n✅ Selected {len(selected_pairs)} function(s):")
            for idx in selected_indices:
                target, _ = pairs[idx - 1]
                print(f"   {idx}. {target.func_name}")
            return selected_pairs

        # Non-interactive mode without preselected functions - test all
        if not interactive:
            print(f"\n✅ Testing all {len(pairs)} function(s)")
            return pairs

        # Interactive mode
        print("\n" + "=" * 60)
        print("SELECT FUNCTIONS TO TEST")
        print("=" * 60)
        print("\nAvailable functions:")

        # Display numbered list of functions
        for i, (target, _) in enumerate(pairs, 1):
            print(f"  {i}. {target.func_name}")

        print(f"\n  0. Test all functions")
        print("\nOptions:")
        print("  - Enter numbers separated by commas (e.g., '1,3,5')")
        print("  - Enter ranges with dash (e.g., '1-3')")
        print("  - Enter '0' or 'all' to test all functions")
        print("  - Press Enter to test all functions")
        print("  - Enter 'q' or 'quit' to cancel")

        while True:
            try:
                user_input = input("\nYour selection: ").strip()

                # Handle empty input (test all)
                if not user_input or user_input in ["0", "all"]:
                    print(f"\n✅ Selected all {len(pairs)} function(s)")
                    return pairs

                # Handle quit
                if user_input.lower() in ["q", "quit"]:
                    print("\n❌ Testing cancelled by user.")
                    return []

                # Parse input
                selected_indices = self._parse_function_selection(
                    user_input, len(pairs)
                )

                if selected_indices is None:
                    print(
                        "⚠️  No valid functions selected. Please try again."
                    )
                    continue

                # Get selected pairs
                selected_pairs = [
                    pairs[idx - 1] for idx in selected_indices
                ]

                # Show selection
                print(
                    f"\n✅ Selected {len(selected_pairs)} function(s):"
                )
                for idx in selected_indices:
                    target, _ = pairs[idx - 1]
                    print(f"   {idx}. {target.func_name}")

                return selected_pairs

            except KeyboardInterrupt:
                print("\n\n❌ Testing cancelled by user.")
                return []
            except Exception as e:
                print(f"⚠️  Error: {e}. Please try again.")
                continue

    def _parse_function_selection(
        self, selection: str, max_index: int
    ) -> list:
        """
        Parse function selection string into list of indices.

        Args:
            selection: Selection string (e.g., "1,2,3" or "1-3" or "all")
            max_index: Maximum valid index

        Returns:
            Sorted list of selected indices (1-based), or None if invalid
        """
        if not selection:
            return None

        # Handle "all" or "0"
        if selection.lower() in ["all", "0"]:
            return list(range(1, max_index + 1))

        selected_indices = set()

        for part in selection.split(","):
            part = part.strip()

            # Handle ranges (e.g., "1-3")
            if "-" in part:
                try:
                    start, end = part.split("-", 1)
                    start_idx = int(start.strip())
                    end_idx = int(end.strip())

                    if start_idx < 1 or end_idx > max_index:
                        print(
                            f"⚠️  Range {start_idx}-{end_idx} is out of bounds (1-{max_index})"
                        )
                        continue

                    selected_indices.update(
                        range(start_idx, end_idx + 1)
                    )
                except ValueError:
                    print(f"⚠️  Invalid range format: '{part}'")
                    continue

            # Handle single numbers
            else:
                try:
                    idx = int(part)
                    if idx == 0:
                        # User selected "0" (all)
                        return list(range(1, max_index + 1))
                    elif 1 <= idx <= max_index:
                        selected_indices.add(idx)
                    else:
                        print(
                            f"⚠️  Number {idx} is out of bounds (1-{max_index})"
                        )
                except ValueError:
                    print(f"⚠️  Invalid number: '{part}'")
                    continue

        return sorted(selected_indices) if selected_indices else None

    def _generate_html_report(
        self,
        test_result,
        a_results,
        b_results,
        strategy,
        config,
        command,
        duration,
        output_path,
    ):
        """Generate HTML report for test results."""
        try:
            from .reporting import HTMLReporter

            reporter = HTMLReporter()
            report_path = reporter.generate_report(
                test_result=test_result,
                a_results=a_results,
                b_results=b_results,
                strategy=strategy,
                config=config,
                command=command,
                duration=duration,
                output_path=output_path,
            )

            self.log.normal(
                f"\n📊 HTML Report generated: {report_path}"
            )
            self.log.normal(
                f"   Open in browser: file://{os.path.abspath(report_path)}"
            )

        except Exception as e:
            self.log.normal(f"\n⚠️  Failed to generate HTML report: {e}")
            import traceback

            self.log.debug(
                f"Report generation error: {traceback.format_exc()}"
            )

    def _build_command_string(
        self, file_a, file_b, func_name, max_examples, seed=None
    ):
        """Build command string for reproduction."""
        cmd = f"python src/run_ab.py --a {file_a} --b {file_b} --func {func_name} --max-examples {max_examples}"
        if seed is not None:
            cmd += f" --seed {seed}"
        return cmd

    def run_base_and_patch_from_repo(
        self,
        repo_url: str,
        base_commit: str,
        patch_content: str,
        func_name: str = None,
        max_examples: int = 200,
        install_deps: bool = True,
        auto_approve: bool = False,
        interactive_select: bool = True,
        selected_functions: str = None,
        report_path: str = None,
        seed: int = None,
    ):
        """
        Run differential testing using base commit + patch approach.

        Instead of parsing the patch file, this method:
        1. Checkouts to base_commit (pre-change state)
        2. Extracts files from the patch
        3. Applies the patch
        4. Compares the two states

        This avoids issues with malformed patch files.

        Args:
            repo_url: Repository URL to clone
            base_commit: Base commit hash (before changes)
            patch_content: Patch content as string
            func_name: Optional filter for specific function name
            max_examples: Maximum number of test examples per function
            install_deps: Whether to install dependencies
            auto_approve: If True, skip user confirmation for strategies
            interactive_select: If True, prompt user to select functions
            selected_functions: Pre-selected function indices
            report_path: Optional path to save HTML report
            seed: Optional random seed for reproducible test generation

        Returns:
            List of test results for each modified function
        """
        import os
        import subprocess
        import tempfile
        import shutil

        # Clone repo and checkout to base commit
        self.log.verbose(
            f"[Orchestrator] Cloning repository and checking out base commit: {base_commit}"
        )
        env = self.project_builder.build_from_url(
            repo_url, base_commit, install_deps=install_deps
        )

        try:
            self.log.verbose(
                f"[Orchestrator] Project cloned to: {env.project_root}"
            )

            # Find test file if exists (for type inference)
            test_file = self._find_test_file(env.project_root)

            # Change to project root
            original_cwd = os.getcwd()
            os.chdir(env.project_root)

            try:
                # Save patch to temporary file
                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".patch", delete=False
                ) as f:
                    f.write(patch_content)
                    patch_file = f.name

                try:
                    # Extract list of modified files from patch
                    self.log.verbose(
                        "[Orchestrator] Extracting modified files from patch"
                    )
                    cmd = ["git", "apply", "--numstat", patch_file]
                    result = subprocess.run(
                        cmd, capture_output=True, text=True
                    )

                    modified_files = []
                    if result.stdout:
                        for line in result.stdout.strip().split("\n"):
                            if line:
                                parts = line.split("\t")
                                if len(parts) >= 3:
                                    modified_files.append(parts[2])

                    self.log.verbose(
                        f"[Orchestrator] Found {len(modified_files)} modified files"
                    )

                    # Create temp directory for file pairs
                    temp_dir = tempfile.mkdtemp(prefix="dt_base_patch_")

                    try:
                        # Save "before" versions (base commit)
                        before_files = {}
                        for file_path in modified_files:
                            if os.path.exists(file_path):
                                before_file = os.path.join(
                                    temp_dir,
                                    f"before_{os.path.basename(file_path)}",
                                )
                                shutil.copy(file_path, before_file)
                                before_files[file_path] = before_file
                                self.log.debug(
                                    f"[Orchestrator] Saved before: {file_path} -> {before_file}"
                                )

                        # Apply patch
                        self.log.verbose(
                            "[Orchestrator] Applying patch"
                        )
                        cmd = ["git", "apply", patch_file]
                        result = subprocess.run(
                            cmd, capture_output=True, text=True
                        )

                        if result.returncode != 0:
                            self.log.normal(
                                f"⚠️  Warning: git apply failed: {result.stderr}"
                            )
                            self.log.normal(
                                "Attempting to apply with 3-way merge..."
                            )
                            cmd = ["git", "apply", "--3way", patch_file]
                            result = subprocess.run(
                                cmd, capture_output=True, text=True
                            )
                            if result.returncode != 0:
                                raise RuntimeError(
                                    f"Failed to apply patch: {result.stderr}"
                                )

                        # Save "after" versions (with patch applied)
                        after_files = {}
                        for file_path in modified_files:
                            if os.path.exists(file_path):
                                after_file = os.path.join(
                                    temp_dir,
                                    f"after_{os.path.basename(file_path)}",
                                )
                                shutil.copy(file_path, after_file)
                                after_files[file_path] = after_file
                                self.log.debug(
                                    f"[Orchestrator] Saved after: {file_path} -> {after_file}"
                                )

                        # Now generate a proper diff from the current working directory changes
                        # Since we've applied the patch, git diff will show the changes
                        self.log.verbose(
                            "[Orchestrator] Generating diff from applied changes"
                        )

                        # Create a diff file from current working directory changes
                        diff_output_file = os.path.join(
                            temp_dir, "applied.diff"
                        )
                        cmd = ["git", "diff", "HEAD"]
                        result = subprocess.run(
                            cmd, capture_output=True, text=True
                        )

                        with open(diff_output_file, "w") as f:
                            f.write(result.stdout)

                        # Parse the diff to find modified functions
                        from .diffpairer import DiffPairer

                        pairer = DiffPairer()

                        self.log.verbose(
                            "[Orchestrator] Parsing diff to find modified functions"
                        )
                        all_pairs = pairer.pair_from_diff_file(
                            diff_output_file,
                            func_name=func_name,
                            project_root=env.project_root,
                        )

                        if not all_pairs:
                            self.log.verbose(
                                "[Orchestrator] No modified functions found"
                            )
                            return []

                        # Let user select which functions to test
                        selected_pairs = self._select_functions_to_test(
                            all_pairs,
                            interactive=interactive_select,
                            preselected=selected_functions,
                        )

                        if not selected_pairs:
                            print(
                                "\n❌ No functions selected for testing."
                            )
                            return []

                        self.log.verbose(
                            f"[Orchestrator] Testing {len(selected_pairs)} selected function(s)"
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
                        generated_reports = []
                        for i, (target, cleanup_pair) in enumerate(
                            selected_pairs, 1
                        ):
                            self.log.verbose(
                                f"[Orchestrator] Testing {i}/{len(selected_pairs)}: {target.func_name}"
                            )

                            # Generate unique report path for each function
                            func_report_path = None
                            if report_path:
                                if len(selected_pairs) > 1:
                                    base, ext = os.path.splitext(
                                        report_path
                                    )
                                    func_report_path = f"{base}_{target.func_name}{ext}"
                                else:
                                    func_report_path = report_path
                            else:
                                # Auto-generate report in project root if not specified
                                instance_id = repo_url.split("/")[
                                    -1
                                ].replace(".git", "")
                                func_report_path = os.path.join(
                                    env.project_root,
                                    f"report_{instance_id}_{target.func_name}.html",
                                )

                            generated_reports.append(func_report_path)

                            try:
                                result = self.run_pair(
                                    file_a=target.file_a,
                                    file_b=target.file_b,
                                    func_name=target.func_name,
                                    max_examples=max_examples,
                                    test_file=test_file,
                                    auto_approve=auto_approve,
                                    report_path=func_report_path,
                                    seed=seed,
                                )
                                results.append(result)
                            finally:
                                cleanup_pair()

                        # Print summary of generated reports
                        if generated_reports and not report_path:
                            self.log.normal("\n📄 Generated Reports:")
                            for report in generated_reports:
                                self.log.normal(f"   • {report}")

                        return results

                    finally:
                        # Cleanup temp directory
                        if os.path.exists(temp_dir):
                            shutil.rmtree(temp_dir)

                finally:
                    # Cleanup patch file
                    if os.path.exists(patch_file):
                        os.unlink(patch_file)

            finally:
                os.chdir(original_cwd)

        finally:
            env.cleanup()
