"""
Deterministic Rules Engine
---------------------------
Evaluates business rules independently of LLM logic.
Rules are loaded from JSON files and evaluated based on customer context.
"""

import json
from typing import Dict, Any, List, Optional
from pathlib import Path


class RulesEngine:
    """Evaluates business rules deterministically based on customer context."""
    
    def __init__(self, rules_path: str):
        """
        Initialize the rules engine with a rules JSON file.
        
        Args:
            rules_path: Path to the rules JSON file
        """
        self.rules_path = Path(rules_path)
        self.rules_data = self._load_rules()
    
    def _load_rules(self) -> Dict[str, Any]:
        """Load rules from JSON file."""
        with open(self.rules_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _evaluate_condition(self, condition: Any, context_value: Any) -> bool:
        """
        Evaluate a single condition against a context value.
        
        Supports:
        - Direct equality: "plan": "Ahorro"
        - Range checks: "scoring": {"min": 4}
        - Max checks: "stops": {"max": 1}
        
        Args:
            condition: The condition from the rule
            context_value: The actual value from customer context
            
        Returns:
            True if condition matches, False otherwise
        """
        # Handle missing context value
        if context_value is None:
            return False
        
        # Handle simple equality
        if not isinstance(condition, dict):
            return condition == context_value
        
        # Handle range conditions
        if "min" in condition:
            if context_value < condition["min"]:
                return False
        
        if "max" in condition:
            if context_value > condition["max"]:
                return False
        
        return True
    
    def _evaluate_rule(self, rule: Dict[str, Any], customer_context: Dict[str, Any]) -> bool:
        """
        Evaluate if a rule's conditions match the customer context.
        All conditions in 'when' must be satisfied (AND logic).
        
        Args:
            rule: The rule to evaluate
            customer_context: Customer context data
            
        Returns:
            True if all conditions match, False otherwise
        """
        when_conditions = rule.get("when", {})
        
        for field, condition in when_conditions.items():
            context_value = customer_context.get(field)
            
            if not self._evaluate_condition(condition, context_value):
                return False
        
        return True
    
    def evaluate(self, customer_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate all rules against customer context and return the decision.
        
        1. Validates required fields.
        2. If fields are missing, returns status: NEED_INFO.
        3. If all fields are present, evaluates rules by priority and returns status: RECOMMENDATION.
        
        Args:
            customer_context: Dictionary containing customer data
            
        Returns:
            Standardized decision dictionary with either status: NEED_INFO or RECOMMENDATION.
        """
        # Step 1: Check for required fields
        required_fields = self.rules_data.get("required_fields", [])
        missing_info_behavior = self.rules_data.get("missing_info_behavior", {})
        
        for field in required_fields:
            value = customer_context.get(field)
            # Consider None, empty string, or placeholder "desconocido" as missing
            if value is None or value == "" or value == "desconocido" or value == "null":
                return {
                    "status": "NEED_INFO",
                    "missing_field": field,
                    "behavior": missing_info_behavior.get("status", "NEED_INFO"),
                    "question_data": missing_info_behavior.get("questions", {}).get(field)
                }

        # Step 2: All required info is present, evaluate rules
        # Sort rules by priority (highest first)
        rules = sorted(
            self.rules_data.get("rules", []),
            key=lambda r: r.get("priority", 0),
            reverse=True
        )
        
        # Collect all matching rules (we may need to merge results)
        matched_rules = []
        for rule in rules:
            if self._evaluate_rule(rule, customer_context):
                matched_rules.append(rule)
        
        if not matched_rules:
            # No rules matched - return default "no match" decision
            return {
                "status": "RECOMMENDATION",
                "decision": "no_match",
                "stop_allowed": None,
                "allowed_actions": [],
                "reason": "no_rules_matched"
            }
        
        # Build consolidated decision from matched rules
        # Start with highest priority rule
        primary_rule = matched_rules[0]
        then_clause = primary_rule.get("then", {})
        
        decision = {
            "status": "RECOMMENDATION",
            "decision": then_clause.get("decision", "unknown"),
            "stop_allowed": then_clause.get("stop_allowed"),
            "allowed_actions": then_clause.get("allowed_actions", []),
            "reason": then_clause.get("reason", "rule_" + primary_rule.get("id", "unknown"))
        }
        
        # Merge additional flags from other matching rules
        for rule in matched_rules:
            then_clause = rule.get("then", {})
            if "allow_stop_0euros" in then_clause:
                decision["allow_stop_0euros"] = then_clause["allow_stop_0euros"]
        
        return decision


def load_rules_engine(process_name: str) -> RulesEngine:
    """
    Factory function to load a rules engine for a specific process.
    
    Args:
        process_name: Name of the process (e.g., "STOP_REPARTO")
        
    Returns:
        RulesEngine instance for the process
    """
    # Construct path to rules file
    base_path = Path(__file__).parent.parent
    rules_path = base_path / process_name.lower() / f"rules_{process_name.lower()}.json"
    
    return RulesEngine(str(rules_path))
