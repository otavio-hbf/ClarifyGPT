# ClarifyGPT-5

### 🚀 Modernizing Requirement Clarification in Code Generation

**ClarifyGPT-5** is an extended replication and modernization of the original [ClarifyGPT framework](https://github.com/ClarifyGPT/ClarifyGPT). This project aims to test the efficacy of the ClarifyGPT framework, which empowers LLMs to ask targeted clarifying questions when facing ambiguous requirements—against the latest generation of Large Language Models.

In addition to updating the model backend, this repository addresses several execution issues present in the original codebase to ensure smoother reproduction of results.

---

### 📖 Project Summary

Large Language Models (LLMs) often struggle with ambiguous or insufficient user requirements, leading to code that deviates from the user's actual intent. **ClarifyGPT** bridges this gap by introducing a "Clarification Loop":

1.  **Ambiguity Detection:** Performs a code consistency check to detect if a requirement is unclear.
2.  **Targeted Questioning:** If ambiguous, it prompts the LLM to ask specific questions to clear up the confusion.
3.  **Refinement & Generation:** It refines the requirement based on user responses and generates the final solution.

**ClarifyGPT-5** brings this workflow to modern LLM architectures, providing a robust testbed for evaluating how newer models handle requirement ambiguity.

---

### 📂 Branch Organization

This repository utilizes a specific branching strategy to manage different experimental configurations and model sizes. To replicate specific experiments or baseline tests, you **must switch to the appropriate branch**.

The available sub-branches are:

- `roda-baseline` (Baseline)
- `roda-baseline-fix-eval` (Baseline with fixed Evaluation)
- `roda-mini-low` (GPT5-Mini w/ Low Reasoning)
- `roda-nano-high`(GPT5-Nano w/ High Reasoning)
- `roda-nano-medium`(GPT5-Nano w/ Medium Reasoning)
- `roda-nano-low` (GPT5-Nano w/ Low Reasoning)
- `clarify-deep` (DeepSeek-V5)

To switch to a branch, use:
```bash
git checkout <branch-name>
# Example:
git checkout roda-baseline-fix-eval
```

### ⚠️ Prerequisites & Constraints

> **Critical Note on Evaluation:**
> The evaluation scripts (calculating Pass@1 metrics) are **limited to Linux OS environments**. Attempting to run the evaluation pipeline on Windows or macOS may result in execution errors.

---

### 🏃 Run & Evaluation

Once you have checked out your desired branch (e.g., `roda-nano-high`), you can follow the original execution workflow.

#### 1. Run ClarifyGPT

Execute the main script to run the clarification framework on benchmarks (HumanEval or MBPP).

```bash
# General Syntax
python src/run_clarify_{model_name}_{benchmark}.py

# Example
python src/run_clarify_chatgpt_mbpp.py

# Calculate MBPP metrics
python evaluation/MBPP/main.py
```

