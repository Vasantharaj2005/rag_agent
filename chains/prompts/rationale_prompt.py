# chains/prompts/rationale_prompt.txt
You are tasked with providing detailed rationale and reasoning for insurance policy answers.

For each answer you provide, explain:

1. BASIS: What specific sections or clauses support this answer
2. INTERPRETATION: How the policy language should be understood
3. IMPLICATIONS: What this means for the policyholder
4. LIMITATIONS: Any restrictions or conditions that apply
5. RELATED TERMS: Other policy provisions that might be relevant

Your rationale should help users understand not just the answer, but why that answer is correct according to the policy terms.

Question: {question}
Answer: {answer}
Context: {context}

Provide detailed rationale: