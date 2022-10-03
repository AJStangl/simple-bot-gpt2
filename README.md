Thread Conversation Language Modeling Fine-Tuning and Generation On Individuals
===

Getting Started
---

This is a simple command line/library for generating a custom gtp2 fine-tuning data and subsequent fine-tuning.

Installation
---

The module can be directly installed through cloning the repository and installing via pip:

```bash
pip install  git+https://github.com/AJStangl/simple-bot-gpt2@master
``` 

Or you can clone the repository and set it up like so:

```bash
git clone https://github.com/AJStangl/simple-bot-gpt2
cd simple-bot-gpt2
python setup.py build
pip install --editable .
```

    Installing collected packages: simple-bot-gpt2
    Running setup.py develop for simple-bot-gpt2
    Successfully installed simple-bot-gpt2-0.0.1


Usage
---

The module can be used in two ways. As a command line utility of as package in src.

CLI Usage
___

```bash
simple-bot-gpt2 --help
```

    Options:
      --help  Show this message and exit.
    
    Commands:
        run-bot         Command for running the bot on a specified sub-reddit
        collect-data    Command for downloading the fine-tuning data
