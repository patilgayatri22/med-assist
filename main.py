import json
from llm_client import ask_llama_json
from llm_toolhouse_client import run_agent
from prompts import SYSTEM_PROMPT, JSON_OUTPUT_INSTRUCTION
from test_scenarios import MEDICAL_SCENARIOS


def run_basic_mode():
    """Run basic LLM mode without tools"""
    print("\n=== MedAssist Basic Mode ===")
    user_prompt = input("Enter medical prompt: ").strip()

    if not user_prompt:
        print("No prompt entered.")
        return

    full_system_prompt = SYSTEM_PROMPT + "\n\n" + JSON_OUTPUT_INSTRUCTION
    response = ask_llama_json(user_prompt, full_system_prompt)

    print("\n🤖 Medical Assistant Response:")
    print(json.dumps(response, indent=2))


def run_toolhouse_mode():
    """Run Toolhouse-enhanced mode with tools"""
    print("\n=== MedAssist Toolhouse Mode ===")

    user_prompt = input("Enter medical scenario: ").strip()

    if not user_prompt:
        print("No scenario entered.")
        return

    try:
        result = run_agent(user_prompt)
        print("\n🏥 Enhanced Medical Assessment:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"❌ Toolhouse assessment failed: {e}")
        print("Falling back to basic mode...")

        # Fallback to basic mode
        full_system_prompt = SYSTEM_PROMPT + "\n\n" + JSON_OUTPUT_INSTRUCTION
        result = ask_llama_json(user_prompt, full_system_prompt)
        print("\n🤖 Basic Assessment:")
        print(json.dumps(result, indent=2))


def run_scenario_test():
    """Test predefined medical scenarios"""
    print("\n=== MedAssist Scenario Testing ===")

    print("Available scenarios:")
    for i, (name, scenario) in enumerate(MEDICAL_SCENARIOS.items(), 1):
        priority = scenario.get('expected_priority', 'unknown')
        critical = '🔴' if scenario.get('safety_critical') else '🟢'
        print(f"  {i}. {name} {critical} ({priority} priority)")

    try:
        choice = int(input("\nSelect scenario (number): ").strip()) - 1
        scenario_names = list(MEDICAL_SCENARIOS.keys())

        if 0 <= choice < len(scenario_names):
            scenario_name = scenario_names[choice]
            scenario_data = MEDICAL_SCENARIOS[scenario_name]

            print(f"\n🔍 Testing scenario: {scenario_name}")
            print(f"📝 Description: {scenario_data['description']}")

            # Try with Toolhouse first, fallback to basic
            full_prompt = f"Medical Scenario: {scenario_data['description']}"
            if scenario_data.get('patient_data'):
                full_prompt += f"\nPatient Data: {json.dumps(scenario_data['patient_data'], indent=2)}"

            try:
                result = run_agent(full_prompt)
                print("\n🏥 Enhanced Assessment:")
                print(json.dumps(result, indent=2))

            except Exception as e:
                print(f"\n⚠️  Toolhouse failed, using basic mode: {e}")

                full_system_prompt = SYSTEM_PROMPT + "\n\n" + JSON_OUTPUT_INSTRUCTION
                response = ask_llama_json(full_prompt, full_system_prompt)

                print("\n🤖 Basic Assessment:")
                print(json.dumps(response, indent=2))
        else:
            print("Invalid selection.")

    except (ValueError, KeyboardInterrupt):
        print("\nCancelled.")


def main():
    """Main application entry point"""
    print("🏥 MedAssist - Medical Robotics Assistant")
    print("===========================================")

    while True:
        print("\nSelect mode:")
        print("1. Basic Mode (Simple LLM responses)")
        print("2. Toolhouse Mode (Enhanced with tools)")
        print("3. Scenario Testing (Test predefined scenarios)")
        print("4. Exit")

        try:
            choice = input("\nEnter choice (1-4): ").strip()

            if choice == '1':
                run_basic_mode()
            elif choice == '2':
                run_toolhouse_mode()
            elif choice == '3':
                run_scenario_test()
            elif choice == '4':
                print("\n👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please enter 1-4.")

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
