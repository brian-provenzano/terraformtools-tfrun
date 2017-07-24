# Simple Terraform Wrapper script

#### This script is a wrapper around terraform in order to help enforce some 'guardrails' for the user to prevent accidents (e.g. accidental 'terraform apply' on production, etc).  I thought it would be useful (it is..), so maybe you will too.

#### See the source code for directory structure setup details and full explanation of usage

#### Example

```bash
tfrun.py plan
```

TODOs - maybe git integration for plan/applys...