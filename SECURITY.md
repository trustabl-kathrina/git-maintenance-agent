# Security Policy

## v0.1 Boundaries

Git Maintenance Agent is a local developer tool, not a sandbox or hosted service. A live run sends allowed repository evidence to the OpenAI API after the caller explicitly passes `--allow-cloud-analysis`. Test execution runs local project code after `--allow-test-execution`.

The tool blocks common credential paths and constrains filesystem, Git, and pytest operations. It does not guarantee that arbitrary project test code is safe. Use it only on repositories you are authorized to inspect and execute.

## Reporting A Vulnerability

Do not open public issues for potential credential exposure, consent bypass, path escape, arbitrary command execution, or unintended patch application. Contact the repository maintainer privately with a minimal reproduction that excludes secrets and private source code.
