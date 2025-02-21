import re
import logging
from typing import Optional, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PatchValidation:
    def __init__(self, model: Any, patch_dir: str = "patch_candidates", faults: Optional[str] = None, language: Optional[str] = None) -> None:
        logger.info("Initializing PatchValidation")
        self.model = model
        self.patch_dir = patch_dir
        self.faults = faults
        self.language = language
        logger.debug(f"Initialized with patch_dir: {patch_dir}, language: {language}")


    def parse_llm_response(self, response: str):
        """Extracts the status, issues, corrections, and explanation from LLM responses consistently."""
        logger.debug("Starting to parse LLM response")
        
        # Normalize response formatting
        response = response.strip()
        logger.debug("Normalized response formatting")

        # Capture Status (GOOD / BAD) robustly
        status_match = re.search(r"(?i)\**\s*status\s*\**\s*[:.]?\s*\**\s*(good|bad)\**", response)
        status = status_match.group(1).upper() if status_match else "UNKNOWN"
        logger.info(f"Extracted status: {status}")

        # Capture Issues, Corrections, and Explanation
        issues_match = re.search(r"(?i)\*\*Issues\**:\*\*\s*(.*?)(?=\n\n\*\*Corrections\*\*|\n\n\*\*Explanation\*\*|$)", response, re.DOTALL)
        corrections_match = re.search(r"(?i)\*\*Corrections\**:\*\*\s*(.*?)(?=\n\n\*\*Explanation\*\*|$)", response, re.DOTALL)
        explanation_match = re.search(r"(?i)\*\*Explanation\**:\*\*\s*(.*)", response, re.DOTALL)

        issues = issues_match.group(1).strip() if issues_match else "None provided"
        corrections = corrections_match.group(1).strip() if corrections_match else "None provided"
        explanation = explanation_match.group(1).strip() if explanation_match else "None provided"

        logger.debug("Extracted issues, corrections, and explanation")
        logger.debug(f"Issues found: {'Yes' if issues != 'None provided' else 'No'}")
        logger.debug(f"Corrections provided: {'Yes' if corrections != 'None provided' else 'No'}")

        return status, issues, corrections, explanation
    def resolve_sytnax_errors(self, code: str):
        logger.debug("Generating syntax error resolution prompt")
        return f"""
        You are a software engineer. Analyze the following code and correct any syntax and grammatical errors.

        **Code:**  
        ```{self.language}
        {code}  
        ```  

        Output:
        ```{self.language}
        // Provide the detailed code implementation here
        ```
        """

    def get_validation_prompt(self, file_content: str):
        logger.debug("Generating validation prompt")
        prompt = f"""
### **Strict Code Review and Fault Verification Task**

#### **Objective:**
You are an expert-level code reviewer with advanced knowledge of `{self.language}`. Your task is to **rigorously analyze** the provided code for correctness, security vulnerabilities, and efficiency. Additionally, this code has previously been modified by an LLM to address specific faults. Your primary goal is to determine whether these faults were fully resolved and to conduct an in-depth review based on strict evaluation criteria.

---

Here is the file to examine:
{file_content}

### **Evaluation Criteria:**

1. **Compilation & Syntax Validation:**  
   - Ensure that the code compiles successfully in `{self.language}` without syntax errors.  
   - If compilation issues exist, identify the exact errors (with line numbers where possible) and suggest corrections.

2. **Security Audit (Covers All Possible Vulnerabilities):**  
   - Identify and report **any** security vulnerabilities in the code, including but not limited to:
     - **Injection Attacks** (SQL injection, command injection, template injection)
     - **Memory Corruption** (buffer overflows, use-after-free, double-free)
     - **Authentication & Authorization Issues** (broken authentication, privilege escalation)
     - **Insecure Data Handling** (hardcoded credentials, weak encryption, improper input validation)
     - **Denial of Service (DoS) Risks** (inefficient loops, uncontrolled recursion, excessive resource consumption)
     - **Race Conditions** (multi-threading issues, improper locking mechanisms)
     - **Supply Chain Risks** (unsafe dependencies, reliance on untrusted libraries)
   - Assess whether secure coding practices were followed for `{self.language}`.

3. **Best Practices & Code Maintainability:**  
   - Ensure the code adheres to `{self.language}`’s best practices:
     - **Modular design**: Proper function/class usage.
     - **Readability**: Proper naming conventions and formatting.
     - **Avoidance of redundant or inefficient logic**.
   - Identify **code smells**, unnecessary complexity, or performance bottlenecks.

4. **Logical & Functional Correctness:**  
   - Verify that the code performs **exactly** as intended without unexpected behavior.
   - Test against potential **edge cases** to determine robustness.
   - Assess **algorithmic efficiency** and suggest improvements if necessary.

5. **Fault Resolution Verification:**  
   - Examine the provided **list of faults** that were previously addressed.  
   - Determine if each issue was **fully resolved, partially resolved, or still present**.  
   - Provide **explicit justification** for each fault's resolution status.

---

### **Response Format (STRICTLY FOLLOW THIS STRUCTURE):**

**Status:** `[GOOD / BAD]`  
*(Choose GOOD if all faults were resolved and the code meets all evaluation criteria. Choose BAD if any issues remain.)*

**Issues:**  
```
[List all detected issues with explanations, or explicitly state "None" if the code is flawless.]
```

**Security Vulnerabilities Found:**  
```
[List all security vulnerabilities present in the code. If none exist, explicitly state "None."]
```

**Corrections:**  
```
[If necessary, provide a corrected version of the code in a properly formatted block, ensuring it remains fully functional, secure, and optimized.]
```

**Explanation:**  
```
[Provide a concise but detailed explanation, linking identified issues to best practices, security concerns, or logical flaws.]
```

---

### **Additional Requirements:**

1. **Code Formatting & Clarity:**  
   - Any modified code must be returned in a **properly formatted** code block.
   - Ensure **syntax highlighting** and **preserve indentation**.

2. **Strict Compilation & Execution Enforcement:**  
   - If errors exist, the corrected version **must** be executable **as-is** in `{self.language}` without further modification.
   - The LLM **must verify that the suggested corrections will compile and run correctly**.

3. **Comprehensive Security Assessment:**  
   - The analysis **must cover all potential vulnerabilities**, even if they were not explicitly mentioned in the faults.
   - **Do not assume the original fault list is exhaustive**—new vulnerabilities may exist.

4. **Precision & Depth:**  
   - Be **highly specific** with identified issues (include line numbers where possible).
   - Avoid generic advice—base all feedback on `{self.language}` best practices and security guidelines.

---
        """
        logger.debug("Validation prompt generated successfully")
        return prompt

    # prompts llm about the current file
    def validate_patches(self):
        logger.info("Starting patch validation process")
        code_content = ""
        try:
            with open(f"{self.patch_dir}/iterative_patch.{self.language}", "r", encoding='utf-8') as file:
                code_content = file.read()
                logger.debug(f"Successfully read file: {self.patch_dir}/iterative_patch.{self.language}")
        except Exception as e:
            logger.error(f"Error reading patch file: {str(e)}")
            raise

        # get validation prompt
        prompt = self.get_validation_prompt(code_content)
        logger.debug("Generated validation prompt")

        response = self.model.generate_response(prompt)
        logger.debug("Received response from model")

        # parse the response to get status and other information
        status, issues, corrections, explanation = self.parse_llm_response(response)
        logger.info(f"Validation complete - Status: {status}")
        
        # return the parsed response regardless of status
        return status, issues, corrections, explanation
