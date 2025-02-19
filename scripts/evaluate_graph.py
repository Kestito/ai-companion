import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

from ai_companion.graph.graph import create_workflow_graph
from ai_companion.graph.state import AICompanionState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TEST_SCENARIOS = [
    {
        "name": "POLA Card Information Request",
        "messages": [
            {"role": "user", "content": "kaip gauti pola kortele?"}
        ],
        "expected_workflow": "conversation_node",
        "expected_rag": True,
        "validation_keywords": ["pola", "kortelė", "gauti"]
    },
    {
        "name": "Weather Question (No RAG)",
        "messages": [
            {"role": "user", "content": "koks dabar oras?"}
        ],
        "expected_workflow": "conversation_node",
        "expected_rag": False,
        "validation_keywords": ["oras", "temperatūra"]
    },
    {
        "name": "POLA Card Discounts",
        "messages": [
            {"role": "user", "content": "kokias nuolaidas suteikia pola kortele?"}
        ],
        "expected_workflow": "conversation_node",
        "expected_rag": True,
        "validation_keywords": ["nuolaida", "pola", "kortelė"]
    },
    {
        "name": "Multi-Turn POLA Conversation",
        "messages": [
            {"role": "user", "content": "kaip gauti pola kortele?"},
            {"role": "assistant", "content": "POLA kortelę galite gauti..."},
            {"role": "user", "content": "o kokias nuolaidas ji duoda?"}
        ],
        "expected_workflow": "conversation_node",
        "expected_rag": True,
        "validation_keywords": ["nuolaida", "pola"]
    }
]

class GraphEvaluator:
    def __init__(self):
        self.workflow = create_workflow_graph()
        self.results_dir = Path("tests/evaluation_results")
        self.results_dir.mkdir(exist_ok=True, parents=True)
    
    def create_base_state(self) -> AICompanionState:
        return {
            "messages": [],
            "metadata": {"session_id": f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}"},
            "memory": {},
            "workflow": None,
            "current_activity": None
        }
    
    def validate_response(self, result: Dict[str, Any], scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the response against scenario expectations"""
        response_text = " ".join(str(msg.get("content", "")) for msg in result.get("messages", []))
        keywords_found = [keyword for keyword in scenario["validation_keywords"] 
                         if keyword.lower() in response_text.lower()]
        
        rag_used = result.get("rag_response", {}).get("has_relevant_info", False)
        
        return {
            "keywords_matched": len(keywords_found) / len(scenario["validation_keywords"]),
            "rag_expectation_met": rag_used == scenario["expected_rag"],
            "workflow_correct": result.get("workflow") == scenario["expected_workflow"],
            "response_coherent": len(response_text.split()) >= 10  # Basic coherence check
        }
    
    async def evaluate_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a single test scenario"""
        state = self.create_base_state()
        state["messages"] = scenario["messages"]
        
        try:
            start_time = datetime.now()
            result = await self.workflow.ainvoke(state, {})
            end_time = datetime.now()
            
            validation_results = self.validate_response(result, scenario)
            
            evaluation = {
                "scenario_name": scenario["name"],
                "success": all(validation_results.values()),
                "execution_time": (end_time - start_time).total_seconds(),
                "validation_results": validation_results,
                "response_messages": result.get("messages", []),
                "error": None
            }
        except Exception as e:
            evaluation = {
                "scenario_name": scenario["name"],
                "success": False,
                "execution_time": None,
                "validation_results": None,
                "response_messages": [],
                "error": str(e)
            }
        
        return evaluation
    
    async def run_evaluation(self, scenarios: List[Dict[str, Any]] = TEST_SCENARIOS):
        """Run evaluation on all test scenarios"""
        results = []
        
        for scenario in scenarios:
            logger.info(f"Evaluating scenario: {scenario['name']}")
            result = await self.evaluate_scenario(scenario)
            results.append(result)
            
            if result["success"]:
                logger.info(f"✓ {scenario['name']} completed successfully")
                logger.info(f"  Time: {result['execution_time']:.2f}s")
                if result["validation_results"]:
                    logger.info(f"  Keyword match: {result['validation_results']['keywords_matched']*100:.0f}%")
            else:
                logger.error(f"✗ {scenario['name']} failed")
                logger.error(f"  Error: {result['error']}")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = self.results_dir / f"graph_evaluation_{timestamp}.json"
        
        with open(results_file, "w", encoding='utf-8') as f:
            json.dump({
                "timestamp": timestamp,
                "total_scenarios": len(scenarios),
                "successful_scenarios": sum(1 for r in results if r["success"]),
                "results": results
            }, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Evaluation results saved to {results_file}")
        return results

async def main():
    evaluator = GraphEvaluator()
    await evaluator.run_evaluation()

if __name__ == "__main__":
    asyncio.run(main()) 