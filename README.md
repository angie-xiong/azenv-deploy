![Tests](.github/workflows/ci.yml/badge.svg)

1. Set up running environment
In your Terminal, please run the [`./scripts/setup_env.sh`](./scripts/setup_env.sh)

2. Create and preview a pulumi stack
In your Terminal,

* User a local file to store pulumi state.

* Run `pulumi login <path/to/repo/root>` to use pulumi existing state file. For example:

    `pulumi login file:///Users/axiong/learning/azenv-deploy`

* Create or change a dir for pulumi stacks

    `mkdir projects/dev` or

    `cd projects/dev`

* (Optional) To create a pulumi project

    `pulumi new` # The secret for the stack `dev` in this project is "xaq2674"

* List existing pulumi stacks

    `pulumi stack ls`

* Select an existing pulumi stack

    `pulumi stack select <stack-name>` # e,g: `pulumi stack select dev`

* To preview an existing pulumi stack

    `pulumi preview`
