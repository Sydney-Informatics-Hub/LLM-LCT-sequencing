# AI Semantic Insights: LLM Toolkit for Analysing Educational Practices and Knowledge Building

## Introduction

This repository provides AI-powered LLM tools for classifying sequencing relations between text clauses for Legitimation Code Theory (LCT). LCT is a framework developed by Prof. Karl Maton for identify and classify the ‘epistemic-semantic density (ESD)’ in English discourse, which is an approach to analyzing knowledge practices in various social fields, including education. LCT is often used to examine the underlying principles that guide knowledge building, curriculum design, pedagogical practices, and the evaluation of student work. Utilising the LCT analytic method, the complexity of knowledge practices and knowledge-building can be conceptualised and revealed from educational texts, such as the lecture transcriptions.

SIH has previously completed the ‘clausing tool’ (project PIPE-156), i.e. combining word-groupings into short, coherent standalone passages, and in turn classifying the clauses as one of the eight predefined types so that the EC can be quantitatively measured, and an information density profile of the text was generated.

This project focuses on implementing the next level of the epistemological condensation of the texts, “sequencing tool”. By combining more than one short passages (clauses), the sequencing patterns affects how the meanings are condensed from more than one passages and transported across passages. Similar to the clausing typology, the sequencing tool has a 3-level hierarchical system that consists of 8 sub-types of sequencing at the finest granularity.

## Overview

### Overview of LLM training and optimisation for development



```mermaid
graph TD


Expert --> LLM-Instructions
Expert --> Sequencing-Definitions
Expert --> Sequencing-Examples
Sequencing-Examples --> Examples-Split
Examples-Split --> Prompt-Examples
Examples-Split --> Test-Examples
Test-Examples --> True-Classification
Test-Examples --> Test-text-input
Test-text-input --> LLM-Model
Prompt-Examples --> Prompt
LLM-Instructions --> Prompt
Sequencing-Definitions --> Prompt
Prompt --> LLM-Model
LLM-Model --> Test-Predictions
True-Classification --> LLM-Optimisation
Test-Predictions --> LLM-Optimisation
LLM-Optimisation --> Expert
LLM-Optimisation --> LLM-Model


```

### Overview of Sequencing tool for production



```mermaid
graph TD

Input-text --> Clausing-Tool
Clausing-Tool --> Clausing-Pairs
Optimised-LLM-Instructions --> LLM-Model
LLM-Model --> Sequencing-Prediction
Sequencing-Prediction --> Annotation-Tool
Clausing-Pairs --> Annotation-Tool
Clausing-Pairs --> LLM-Model
Annotation-Tool --> Sequencing-Classification
User-Input --> Annotation-Tool
Sequencing-Classification --> EC-Analysis 
Annotation-Tool --> Clausing-Pairs
```

## Functionality

The aim of the LCT analysis tool is to provide researchers an automatic classification system that detects and identifies the sequencing types of combination of passages (clauses). Existing large language models (LLMs), such as OpenAI GPT, are applied for automatic sequencing classification.

## References

- Maton, Karl, and Yaegan J. Doran. "Condensation: A translation device for revealing complexity of knowledge practices in discourse, part 2—clausing and sequencing." Onomázein (2017): 77-110

## Attribution and Acknowledgement
Acknowledgments are an important way for us to demonstrate the value we bring to your research. Your research outcomes are vital for ongoing funding of the Sydney Informatics Hub.

If you make use of this software for your research project, please include the following acknowledgment:

“This research was supported by the Sydney Informatics Hub, a Core Research Facility of the University of Sydney."

