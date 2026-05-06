---
name: project-overview-skill
description: Project overview and goals. Used as context to understand what is being created and why.

---

# Generative Adversarial Networks (GAN) for Planning and Implementation

The goal of this project is to evaluate two approaches to the Generative Adversarial Networks pattern for code creation. This pattern uses separate agents to create the solution and a second agent to evaluate what was created. If the evaluator judges the solution to be inadequate, then it is returned to the first agent with suggestions for improvement. When the evaluator is satisfied with the solution, the loop ends and the process is complete.

## Approaches

1. Generator plans and implements the solution and the Evaluator only looks at the implementation code; this has a single generator-evaluator loop
2. Generator submits its plan to the Evaluator and only after the Evaluator approves the plan will it be implemented; this has two evaluator-generator loops (one for the plan and a second for the implementation)

## Components

### Main Components

The Planner participates in both approaches — it generates the contract in both flows. The plan-review loop (Approach 2) adds a second evaluator-generator cycle specifically for the plan before implementation begins.

1. Planner - creates the specifications (a.k.a. “spec”) that defines the work to be completed based on the prompt
2. Generator - works with the planner to AGREE on a final spec and then writes the code to implement the solution
3. Evaluator - evaluates the work completed by the Generator and decides if it is acceptable as-is or if it needs more work

### Supporting Components

1. Logger - keep track of the Generator-Evaluator loop and logs statistics about their conversations
2. Harness - orchestrates the steps in the process (see details below for the actual steps)


## Steps with NO planning loop

1. User enters a prompt explaining a task to complete what to build
2. PLANNER along with the GENERATOR generate a “contract” (the agreed-upon spec defining the task structure and acceptance criteria) which defines how the task will be structured and evaluated for completeness
3. GENERATOR completes work per the contract and completes a build
4. EVALUATOR runs completed work and evaluates the results versus the original task
  - IF the EVALUATOR determines the solution is good quality code that fulfills the task then move to step 5 (LOG)
  - ELSE the EVALUATOR “fails” the effort then it supplies reasons why plus suggested improvements and go back to step 3 to try again
5. LOG results of token usage and generator-evaluator back and forth

## Steps with planning loop

1. User enters a prompt explaining a task to complete what to build
2. PLANNER along with the GENERATOR generate a “contract” (the agreed-upon spec defining the task structure and acceptance criteria) which defines how the task will be structured and evaluated for completeness
3. GENERATOR PLAN creates a plan to complete the task
4. EVALUATOR evaluates the quality of the plan and scores it
  - IF the EVALUATOR determines the plan is an efficient approach to complete the task then move to step 5
  - ELSE the EVALUATOR “fails” the effort then it supplies reasons why plus suggested improvements and go back to step 3 to try again
NOTE: this is a good spot for Human in the Loop to approve the final plan
5. GENERATOR IMPLEMENTS completes work per the contract (Build + Git Commit)
6. EVALUATOR (Runs and Scores)
  - IF the EVALUATOR determines the solution is good quality code that fulfills the task then move to step 7 (LOG)
  - ELSE the EVALUATOR “fails” the effort then it supplies reasons why plus suggested improvements and go back to step 5 to try again
7. LOG results of token usage and generator-evaluator back and forth


## Additional Resources

[Adversarial Process details](../adversarial-process-skill/SKILL.md)
