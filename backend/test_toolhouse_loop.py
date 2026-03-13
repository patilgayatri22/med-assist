#!/usr/bin/env python3
"""
Test script for Toolhouse LLM integration with medical scenarios
"""

import json
from llm_toolhouse_client import ToolhouseLLMClient
from scenarios import MEDICAL_SCENARIOS


def test_basic_toolhouse_connection():
    """Test basic connection to Toolhouse"""
    print("=== Testing Toolhouse Connection ===")

    try:
        client = ToolhouseLLMClient()
        tools = client.get_available_tools()

        print(f"✅ Connected to Toolhouse")
        print(f"📋 Available tools: {len(tools)}")

        for tool in tools[:3]:  # Show first 3 tools
            print(f"  - {tool.get('name', 'Unknown')}: {tool.get('description', 'No description')}")

        return True

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


def test_simple_medical_query():
    """Test simple medical query without tools"""
    print("\n=== Testing Simple Medical Query ===")

    try:
        client = ToolhouseLLMClient()

        system_prompt = "You are a medical robotics assistant. Provide safe medical guidance."
        user_message = "A patient has a temperature of 102°F. What should I monitor?"

        result = client.chat_with_tools(
            user_message=user_message,
            system_prompt=system_prompt,
            max_iterations=1
        )

        print(f"🤖 Response: {result['final_response']}")
        print(f"🔄 Iterations: {result['iterations']}")
        print(f"🛠️  Tool calls: {len(result['tool_calls'])}")

        return True

    except Exception as e:
        print(f"❌ Query failed: {e}")
        return False


def test_medical_scenario_with_tools():
    """Test medical scenario that might require tools"""
    print("\n=== Testing Medical Scenario with Tools ===")

    try:
        client = ToolhouseLLMClient()

        scenario = """
        Patient ID: 204
        Vital Signs:
        - Temperature: 101.5°F
        - Heart Rate: 110 bpm
        - Blood Pressure: 140/90 mmHg
        - Oxygen Saturation: 96%

        Patient reports chest pain and shortness of breath.
        What assessment and actions should the robot take?
        """

        result = client.medical_assessment_with_tools(
            scenario=scenario,
            patient_data={
                "patient_id": "204",
                "age": 65,
                "medical_history": ["hypertension", "diabetes"],
                "current_medications": ["lisinopril", "metformin"]
            }
        )

        print(f"🏥 Medical Assessment:")
        print(f"Response: {result['final_response']}")
        print(f"\n🔄 Processing Details:")
        print(f"  - Iterations: {result['iterations']}")
        print(f"  - Tool calls made: {len(result['tool_calls'])}")

        if result['tool_calls']:
            print(f"\n🛠️  Tools Used:")
            for i, tool_call in enumerate(result['tool_calls'], 1):
                print(f"  {i}. {tool_call['tool']}")
                print(f"     Parameters: {tool_call['parameters']}")
                print(f"     Result: {tool_call['result']}")

        return True

    except Exception as e:
        print(f"❌ Medical scenario test failed: {e}")
        return False


def test_medication_mismatch_scenario():
    """Test the medication mismatch scenario from earlier"""
    print("\n=== Testing Medication Mismatch Scenario ===")

    try:
        client = ToolhouseLLMClient()

        scenario = "A robot scanned acetaminophen 500mg, but the patient order says ibuprofen 200mg. What should it do?"

        result = client.medical_assessment_with_tools(
            scenario=scenario,
            patient_data={
                "patient_id": "104",
                "ordered_medication": "ibuprofen 200mg",
                "scanned_medication": "acetaminophen 500mg"
            }
        )

        print(f"💊 Medication Safety Assessment:")
        print(f"Response: {result['final_response']}")

        if result['tool_calls']:
            print(f"\n🛠️  Tools consulted:")
            for tool_call in result['tool_calls']:
                print(f"  - {tool_call['tool']}: {tool_call['result']}")
        else:
            print("  - No additional tools were needed for this assessment")

        return True

    except Exception as e:
        print(f"❌ Medication scenario test failed: {e}")
        return False


def test_multiple_scenarios():
    """Test multiple scenarios from scenarios.py"""
    print("\n=== Testing Multiple Medical Scenarios ===")

    try:
        client = ToolhouseLLMClient()

        for scenario_name, scenario_data in MEDICAL_SCENARIOS.items():
            print(f"\n🔍 Testing: {scenario_name}")

            result = client.medical_assessment_with_tools(
                scenario=scenario_data["description"],
                patient_data=scenario_data.get("patient_data")
            )

            print(f"  ✅ Completed in {result['iterations']} iterations")
            print(f"  🛠️  Used {len(result['tool_calls'])} tools")

            # Show brief response
            response = result['final_response']
            if len(response) > 150:
                response = response[:150] + "..."
            print(f"  💡 Response: {response}")

        return True

    except Exception as e:
        print(f"❌ Multiple scenarios test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("🏥 MedAssist Toolhouse Integration Tests\n")

    tests = [
        test_basic_toolhouse_connection,
        test_simple_medical_query,
        test_medical_scenario_with_tools,
        test_medication_mismatch_scenario,
        test_multiple_scenarios
    ]

    passed = 0
    total = len(tests)

    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_func.__name__} failed")
        except Exception as e:
            print(f"❌ {test_func.__name__} crashed: {e}")

        print("-" * 50)

    print(f"\n📊 Test Results: {passed}/{total} passed")

    if passed == total:
        print("🎉 All tests passed!")
    else:
        print(f"⚠️  {total - passed} tests failed")


if __name__ == "__main__":
    main()