[![REUSE status](https://api.reuse.software/badge/github.com/SAP/json-merger-and-symbol-interpolator)](https://api.reuse.software/info/github.com/SAP/json-merger-and-symbol-interpolator)

# json-merger-and-symbol-interpolator

## About this project

Command line tools to merge json files and to replace symbols in json files.

When shared JSON data is copied to different files, any changes to that data must be made in each file where it was copied. This is tedious and error prone; better to change shared JSON data in one place only. These three Python programs, mergejson.py, mergeall.py and factorjson.py, offer alternatives to copying so that shared JSON data can be changed centrally.

There is a detailed user guide here: https://github.com/SAP/json-merger-and-symbol-interpolator/blob/main/user-guide.md

## Requirements and Setup

### Users

Install
- Python3

Read the [User Guide](user-guide.md).

### Developers

Install
- Python3
- PyLint (hint: `pip install pylint`) static code checker.
- YAPF (hint: `pip install yapf`) code formatter.
- 3rd party lib jcs (hint: `pip install jcs`) for unit testing, to canonicalize expected and actual json before comparison.

From the location where git cloned `json-merger-and-symbol-interpolator/py`, run all the unit tests: `python -m unittest discover -v -b`.

When writing code:
- try to follow this [python style guide](https://google.github.io/styleguide/pyguide.html).
- format it using `yapf --style=google -i --no-local-style --verbose <sourcefile>`.
- pylint scores must be perfect 10.00/10, with `--rcfile=json-merger-and-symbol-interpolator/py/pylint.rc` (when unavoidable, `#pylint: disable=` is allowed).

## Support, Feedback, Contributing

This project is open to feature requests/suggestions, bug reports etc. via [GitHub issues](https://github.com/SAP/json-merger-and-symbol-interpolator/issues). Contribution and feedback are encouraged and always welcome. For more information about how to contribute, the project structure, as well as additional contribution information, see our [Contribution Guidelines](CONTRIBUTING.md).

## Security / Disclosure
If you find any bug that may be a security problem, please follow our instructions at [in our security policy](https://github.com/SAP/json-merger-and-symbol-interpolator/security/policy) on how to report it. Please do not create GitHub issues for security-related doubts or problems.

## Code of Conduct

We as members, contributors, and leaders pledge to make participation in our community a harassment-free experience for everyone. By participating in this project, you agree to abide by its [Code of Conduct](https://github.com/SAP/.github/blob/main/CODE_OF_CONDUCT.md) at all times.

## Licensing

Copyright 2024 SAP SE or an SAP affiliate company and json-merger-and-symbol-interpolator contributors. Please see our [LICENSE](LICENSE) for copyright and license information. Detailed information including third-party components and their licensing/copyright information is available [via the REUSE tool](https://api.reuse.software/info/github.com/SAP/json-merger-and-symbol-interpolator).
