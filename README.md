<!-- Improved compatibility of back to top link: See: https://github.com/othneildrew/Best-README-Template/pull/73 -->
<a id="readme-top"></a>

<!-- PROJECT SHIELDS -->
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]



<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/hsethuse-afk/Practicum-AWS-DiffTest">
    <img src="images/logo.png" alt="Logo" width="80" height="80">
  </a>

<h3 align="center">PyDiffer</h3>

  <p align="center">
    A property-based differential testing framework using Hypothesis for automatic test generation and comparison
    <br />
    <a href="https://github.com/hsethuse-afk/Practicum-AWS-DiffTest"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/hsethuse-afk/Practicum-AWS-DiffTest">View Demo</a>
  </p>
</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#code-structure">Code Structure</a></li>
    <li><a href="#benchmarks">Benchmarks</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

<!-- [![Product Name Screen Shot][product-screenshot]](https://example.com) -->

PyDiffer is a property-based differential testing framework that automatically discovers behavioral differences between two versions of Python code. It leverages Hypothesis for intelligent test generation and RightTyper for automatic type inference, making it easy to detect regressions and verify code equivalence.

### Key Features

- **Automatic Type Discovery** - Infers types from test files using RightTyper when annotations are missing
- **Property-Based Testing** - Generates test inputs using Hypothesis strategies
- **Class Method Support** - Tests both module-level functions and class methods with intelligent instance generation
- **HTML Reports** - Interactive, shareable HTML reports with search, filtering, and collapsible sections
- **Coverage Tracking** - Optional code coverage reporting with Slipcover integration
- **Git Integration** - Compare functions across git commits
- **Dark Mode** - HTML reports automatically adapt to system theme preferences

<p align="right">(<a href="#readme-top">back to top</a>)</p>



### Built With

* [![Hypothesis][Hypothesis]][Hypothesis-url]
* [![RightTyper][RightTyper]][RightTyper-url]
* [![Python][Python]][Python-url]
* Slipcover
* Jinja2

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- GETTING STARTED -->
## Getting Started

Follow these steps to get PyDiffer up and running on your local machine.

### Prerequisites

* Python 3.11 or higher
* pip (Python package manager)

### Installation

1. Clone the repo
   ```sh
   git clone https://github.com/hsethuse-afk/Practicum-AWS-DiffTest.git
   ```
2. Navigate to the project directory
   ```sh
   cd Practicum-AWS-DiffTest
   ```
3. Create a virtual environment (recommended)
   ```sh
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
4. Install dependencies
   ```sh
   pip install hypothesis jinja2 slipcover righttyper
   ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- USAGE EXAMPLES -->
## Usage

### Basic Usage - Module Functions

```bash
cd src
python run_ab.py --a testsample/a.py --b testsample/b.py --func has_close_elements
```

### With Type Inference

```bash
python run_ab.py --a a.py --b b.py --func my_function --test-file test.py
```

### Testing Class Methods

```bash
python run_ab.py \
  --a calculator_v1.py \
  --b calculator_v2.py \
  --func add \
  --max-examples 500
```

### Generating HTML Reports

```bash
python run_ab.py \
  --a calculator_v1.py \
  --b calculator_v2.py \
  --func add \
  --max-examples 500 \
  --report my_report.html
```

### Run HumanEval Task by ID

```bash
cd src
python run_by_taskid.py --t HumanEval/10
```

### Command-Line Options

| Option | Description |
|--------|-------------|
| `--a PATH` | Path to first version of the code |
| `--b PATH` | Path to second version of the code |
| `--func NAME` | Function name to test |
| `--max-examples N` | Number of test cases to generate (default: 200) |
| `--seed N` | Random seed for reproducibility |
| `--test-file PATH` | Test file for type inference |
| `--report PATH` | Generate HTML report at specified path |
| `--auto-approve` | Skip strategy confirmation prompt |
| `--log MODE` | Logging: `s`ilent, `n`ormal, `v`erbose, `d`ebug |
| `--coverage` | Generate coverage report |

_For more examples, please refer to the [Documentation](https://github.com/hsethuse-afk/Practicum-AWS-DiffTest)_

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CODE STRUCTURE -->
## Code Structure

| Document | Description |
|----------|-------------|
| [Architecture Overview](docs/architecture.md) | High-level system design and component interactions |
| [Orchestrator](docs/orchestrator.md) | Define and execute workflow for running the differential testing framework |
| [Harness](docs/harness.md) |  |
| [Diff-Pairer](docs/diff-pairer.md) |  |
| [Type Inference](docs/type-inference.md) | Pluggable type inference engine, current implementation focuses on RightTyper integration |
| [Strategy System](docs/strategy-system.md) | How Hypothesis strategies are generated and customized |
| [Test Runner](docs/test-runner.md) | Core differential testing execution flow |
| [Comparator](docs/comparator.md) | Compare results from Test Runner to identify behavior differences |
| [Report Generation](docs/report-generation.md) | HTML report templating and output formats |
| [Coverage Integration](docs/coverage.md) | Slipcover integration for code coverage tracking |

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- BENCHMARKS -->
## Benchmarks

PyDiffer utilized code generation benchmarks to test the abilities to detect behavior differences

### [HumanEval](https://github.com/openai/human-eval)

| Metric | Value |
|--------|-------|
| Tasks Evaluated | 164 |
| Task Supported | 150 |
| Task Passed | 150 |

### [SWE-bench](https://www.swebench.com/)

| Metric | Value |
|--------|-------|
| Tasks Evaluated | TBD |
| Task Supported | TBD |
| Task Passed | TBD |

For detailed benchmark results and methodology, see [docs/benchmarks.md](docs/benchmarks.md).

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Top contributors:

<a href="https://github.com/hsethuse-afk/Practicum-AWS-DiffTest/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=hsethuse-afk/Practicum-AWS-DiffTest" alt="contrib.rocks image" />
</a>



<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTACT -->
## Contact

Project Link: [https://github.com/hsethuse-afk/Practicum-AWS-DiffTest](https://github.com/hsethuse-afk/Practicum-AWS-DiffTest)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

* [Hypothesis](https://hypothesis.works/) - Property-based testing library
* [RightTyper](https://github.com/RightTyper/RightTyper) - Type inference tool by AWS
* [Slipcover](https://github.com/plasma-umass/slipcover) - Code coverage tool
* [Best-README-Template](https://github.com/othneildrew/Best-README-Template)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/hsethuse-afk/Practicum-AWS-DiffTest.svg?style=for-the-badge
[contributors-url]: https://github.com/hsethuse-afk/Practicum-AWS-DiffTest/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/hsethuse-afk/Practicum-AWS-DiffTest.svg?style=for-the-badge
[forks-url]: https://github.com/hsethuse-afk/Practicum-AWS-DiffTest/network/members
[stars-shield]: https://img.shields.io/github/stars/hsethuse-afk/Practicum-AWS-DiffTest.svg?style=for-the-badge
[stars-url]: https://github.com/hsethuse-afk/Practicum-AWS-DiffTest/stargazers
[issues-shield]: https://img.shields.io/github/issues/hsethuse-afk/Practicum-AWS-DiffTest.svg?style=for-the-badge
[issues-url]: https://github.com/hsethuse-afk/Practicum-AWS-DiffTest/issues
[license-shield]: https://img.shields.io/github/license/hsethuse-afk/Practicum-AWS-DiffTest.svg?style=for-the-badge
[license-url]: https://github.com/hsethuse-afk/Practicum-AWS-DiffTest/blob/master/LICENSE.txt
[product-screenshot]: images/screenshot.png
[Hypothesis]: https://img.shields.io/badge/Hypothesis-BD1C2B?style=for-the-badge&logo=python&logoColor=white
[Hypothesis-url]: https://hypothesis.works/
[RightTyper]: https://img.shields.io/badge/RightTyper-FF9900?style=for-the-badge&logo=amazon-aws&logoColor=white
[RightTyper-url]: https://github.com/RightTyper/RightTyper
[Python]: https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white
[Python-url]: https://www.python.org/
