from llm_client import ask_llama, ask_llama_json
from medassist.prompts_old import SYSTEM_PROMPT, JSON_OUTPUT_INSTRUCTION


def test_basic_response():
    prompt = "Say hello in one short sentence."
    response = ask_llama(prompt, SYSTEM_PROMPT)
    print("\n=== BASIC RESPONSE ===")
    print(response)


def test_medassist_json():
    user_prompt = """
A robot is asked to deliver ibuprofen 200mg to patient ID 1042.
The medication barcode scan matches ibuprofen 200mg.
The patient wristband scan failed.
What should the robot do next?
""".strip()

    full_system_prompt = SYSTEM_PROMPT + "\n\n" + JSON_OUTPUT_INSTRUCTION

    response = ask_llama_json(user_prompt, full_system_prompt)

    print("\n=== JSON RESPONSE ===")
    print(response)


if __name__ == "__main__":
    test_basic_response()
    test_medassist_json()