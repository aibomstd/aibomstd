#!/usr/bin/env python3
"""
CI Runner for aibomstd
Validates AIBOM against policies, detects violations, calculates risk score
"""

import json
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml

class AIBOMValidator:
    """Validates AIBOM against policies and calculates risk"""
    
    def __init__(self, aibom_path: str, config_path: Optional[str] = None):
        """Initialize validator with AIBOM and optional config"""
        self.aibom_path = Path(aibom_path)
        self.config_path = Path(config_path) if config_path else None
        self.aibom = self._load_aibom()
        self.config = self._load_config()
        self.violations: List[Dict[str, Any]] = []
        self.risk_score = 0
    
    def _load_aibom(self) -> Dict[str, Any]:
        """Load AIBOM JSON"""
        if not self.aibom_path.exists():
            print(f"❌ AIBOM not found: {self.aibom_path}")
            sys.exit(1)
        
        with open(self.aibom_path) as f:
            return json.load(f)
    
    def _load_config(self) -> Dict[str, Any]:
        """Load policy config from YAML/JSON"""
        if not self.config_path or not self.config_path.exists():
            # Return default policies if no config
            return self._default_policies()
        
        with open(self.config_path) as f:
            if self.config_path.suffix in ['.yml', '.yaml']:
                return yaml.safe_load(f)
            else:
                return json.load(f)
    
    def _default_policies(self) -> Dict[str, Any]:
        """Default security policies"""
        return {
            'policies': [
                {
                    'name': 'no_unknown_model_origin',
                    'severity': 'high',
                    'description': 'All models must have documented origin',
                    'check': lambda c: self._check_model_origin(c)
                },
                {
                    'name': 'data_residency_declared',
                    'severity': 'high',
                    'description': 'Data residency must be declared for external APIs',
                    'check': lambda c: self._check_residency(c)
                },
                {
                    'name': 'framework_vulnerability_check',
                    'severity': 'medium',
                    'description': 'ML frameworks should not have known vulnerabilities',
                    'check': lambda c: self._check_framework_vulns(c)
                },
            ]
        }
    
    def _check_model_origin(self, component: Dict) -> List[str]:
        """Check if model has documented origin"""
        violations = []
        models = self.aibom.get('components', {}).get('models', [])
        
        for model in models:
            if not model.get('origin') or model['origin'] == 'unknown':
                violations.append(f"Model '{model.get('name')}' has undocumented origin")
        
        return violations
    
    def _check_residency(self, component: Dict) -> List[str]:
        """Check if data residency is declared for external APIs"""
        violations = []
        apis = self.aibom.get('components', {}).get('api-clients', [])
        
        for api in apis:
            if api.get('type') == 'external':
                if not api.get('data-residency-declared'):
                    violations.append(
                        f"External API '{api.get('name')}' has no data residency declaration"
                    )
        
        return violations
    
    def _check_framework_vulns(self, component: Dict) -> List[str]:
        """Check frameworks for known vulnerabilities (simplified)"""
        violations = []
        frameworks = self.aibom.get('components', {}).get('frameworks', [])
        
        # Known vulnerable versions (simplified example)
        known_vulns = {
            'torch': ['1.12.0', '1.12.1'],  # Example
            'tensorflow': ['2.9.0'],  # Example
        }
        
        for fw in frameworks:
            name = fw.get('name', '').lower()
            version = fw.get('version', '')
            
            if name in known_vulns and version in known_vulns[name]:
                violations.append(
                    f"Framework '{name}' v{version} has known vulnerabilities. "
                    f"Consider upgrading."
                )
        
        return violations
    
    def validate(self) -> Dict[str, Any]:
        """Run all validations and return results"""
        print("🔍 Running policy validations...")
        
        all_violations = []
        
        # Run checks
        if 'models' in self.aibom.get('components', {}):
            all_violations.extend(self._check_model_origin(self.aibom))
        
        if 'api-clients' in self.aibom.get('components', {}):
            all_violations.extend(self._check_residency(self.aibom))
        
        if 'frameworks' in self.aibom.get('components', {}):
            all_violations.extend(self._check_framework_vulns(self.aibom))
        
        self.violations = [
            {
                'id': i,
                'message': v,
                'severity': 'medium',
                'component': v.split("'")[1] if "'" in v else 'unknown'
            }
            for i, v in enumerate(all_violations)
        ]
        
        # Calculate risk score (0-100)
        self.risk_score = min(100, len(self.violations) * 10 + self._component_risk())
        
        print(f"  Found {len(self.violations)} policy issues")
        print(f"  Risk score: {self.risk_score}/100")
        
        return {
            'valid': len(self.violations) == 0,
            'violations': self.violations,
            'violation_count': len(self.violations),
            'risk_score': self.risk_score,
            'components_scanned': {
                'models': len(self.aibom.get('components', {}).get('models', [])),
                'datasets': len(self.aibom.get('components', {}).get('datasets', [])),
                'frameworks': len(self.aibom.get('components', {}).get('frameworks', [])),
                'api-clients': len(self.aibom.get('components', {}).get('api-clients', [])),
            }
        }
    
    def _component_risk(self) -> int:
        """Calculate base risk from component types"""
        risk = 0
        components = self.aibom.get('components', {})
        
        # External API clients increase risk
        risk += len(components.get('api-clients', [])) * 2
        
        # Undeclared data sources increase risk
        datasets = components.get('datasets', [])
        for ds in datasets:
            if not ds.get('source') or ds['source'] == 'unknown':
                risk += 5
        
        return min(50, risk)


def main():
    parser = argparse.ArgumentParser(
        description='Validate AIBOM against policies'
    )
    parser.add_argument('--aibom', required=True, help='Path to AIBOM JSON')
    parser.add_argument('--config', help='Path to policy config (YAML/JSON)')
    parser.add_argument('--output-violations', help='Output violations to JSON file')
    parser.add_argument('--policy-mode', choices=['warn', 'fail', 'audit'],
                       default='warn', help='Policy enforcement mode')
    
    args = parser.parse_args()
    
    # Validate AIBOM
    validator = AIBOMValidator(args.aibom, args.config)
    results = validator.validate()
    
    # Output violations if requested
    if args.output_violations:
        output_path = Path(args.output_violations)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"✅ Violations written to {output_path}")
    
    # Exit code based on policy mode
    if args.policy_mode == 'fail' and results['violation_count'] > 0:
        sys.exit(1)
    
    sys.exit(0)


if __name__ == '__main__':
    main()
