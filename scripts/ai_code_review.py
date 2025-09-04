#!/usr/bin/env python3
"""
AI Code Review Script with Ollama Integration
Performs intelligent code analysis using AI and provides actionable feedback
"""

import os
import sys
import ast
import subprocess
import json
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional
import argparse

class AICodeReviewer:
    def __init__(self, path: str, rules: List[str], ollama_url: str = "http://localhost:11434"):
        self.path = Path(path)
        self.rules = rules
        self.ollama_url = ollama_url
        self.issues = []
        self.suggestions = []
        self.ai_insights = []
        
    def run_review(self) -> Dict[str, Any]:
        """Run comprehensive AI-powered code review"""
        print("🔍 Starting AI Code Review with Ollama Integration...")
        
        # Check Ollama availability
        if not self._check_ollama_connection():
            print("⚠️  Ollama not available, falling back to static analysis only")
            return self._run_static_review()
        
        # Analyze Python files with AI (excluding virtual environments and other non-project files)
        python_files = self._get_project_python_files()
        if python_files:
            self._analyze_python_files_with_ai(python_files)
        
        # Check for common issues
        self._check_common_issues()
        
        # Generate AI-powered report
        return self._generate_ai_report()
    
    def _get_project_python_files(self) -> List[Path]:
        """Get Python files from the project, excluding virtual environments and other non-project files"""
        # Directories to exclude
        exclude_dirs = {
            '.venv', 'venv', 'env', 'ENV', 'env.bak', 'venv.bak',
            '.git', '.svn', '.hg',
            '__pycache__', '.pytest_cache', '.coverage',
            'node_modules', 'bower_components',
            'build', 'dist', 'target',
            '.mypy_cache', '.ruff_cache',
            'migration-env',  # Your specific migration environment
            'k8s-job-generator-env',  # Additional virtual environment
            'test_env',  # Another virtual environment
            '*-env'  # Pattern for any directory ending with -env
        }
        
        python_files = []
        for file_path in self.path.rglob("*.py"):
            # Skip if any parent directory is in exclude list
            skip_file = False
            for exclude_dir in exclude_dirs:
                if exclude_dir in file_path.parts:
                    skip_file = True
                    break
                # Handle pattern matching for *-env
                if exclude_dir == '*-env':
                    for part in file_path.parts:
                        if part.endswith('-env'):
                            skip_file = True
                            break
                    if skip_file:
                        break
            
            if skip_file:
                continue
            python_files.append(file_path)
        
        print(f"📁 Found {len(python_files)} Python files (excluding virtual environments and build artifacts)")
        return python_files

    def _check_ollama_connection(self) -> bool:
        """Check if Ollama is available and responding"""
        try:
            print(f"🔍 Checking Ollama connection to {self.ollama_url}...")
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            print(f"📡 Ollama response status: {response.status_code}")
            if response.status_code == 200:
                print("✅ Ollama connection successful!")
                return True
            else:
                print(f"⚠️  Ollama returned status {response.status_code}")
                return False
        except requests.exceptions.ConnectionError as e:
            print(f"❌ Ollama connection error: {e}")
            return False
        except requests.exceptions.Timeout as e:
            print(f"⏰ Ollama connection timeout: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error checking Ollama: {e}")
            return False
    
    def _run_static_review(self) -> Dict[str, Any]:
        """Fallback to static analysis only"""
        print("📝 Running static analysis...")
        
        # Analyze Python files (excluding virtual environments)
        python_files = self._get_project_python_files()
        if python_files:
            self._analyze_python_files(python_files)
        
        # Check for common issues
        self._check_common_issues()
        
        # Generate report
        return self._generate_report()
    
    def _analyze_python_files_with_ai(self, files: List[Path]):
        """Analyze Python files using AI for intelligent insights"""
        print(f"🤖 AI-analyzing {len(files)} Python files...")
        
        # Sample files for AI analysis (to avoid overwhelming the model)
        sample_files = files[:min(10, len(files))]  # Analyze up to 10 files with AI
        
        for file_path in sample_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Get AI insights for this file
                ai_analysis = self._get_ai_analysis(file_path, content)
                if ai_analysis:
                    self.ai_insights.append(ai_analysis)
                
                # Also run static analysis
                try:
                    tree = ast.parse(content)
                    self._analyze_ast(tree, file_path)
                except SyntaxError as e:
                    self.issues.append({
                        'file': str(file_path),
                        'type': 'syntax_error',
                        'line': e.lineno,
                        'message': f"Syntax error: {e.msg}"
                    })
                    
            except Exception as e:
                self.issues.append({
                    'file': str(file_path),
                    'type': 'read_error',
                    'message': f"Could not read file: {e}"
                })
        
        # Static analysis for remaining files
        remaining_files = files[len(sample_files):]
        if remaining_files:
            print(f"📝 Running static analysis on {len(remaining_files)} additional files...")
            for file_path in remaining_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    try:
                        tree = ast.parse(content)
                        self._analyze_ast(tree, file_path)
                    except SyntaxError as e:
                        self.issues.append({
                            'file': str(file_path),
                            'type': 'syntax_error',
                            'line': e.lineno,
                            'message': f"Syntax error: {e.msg}"
                        })
                        
                except Exception as e:
                    self.issues.append({
                        'file': str(file_path),
                        'type': 'read_error',
                        'message': f"Could not read file: {e}"
                    })
    
    def _get_ai_analysis(self, file_path: Path, content: str) -> Optional[Dict[str, Any]]:
        """Get AI-powered analysis of a file using Ollama"""
        try:
            # Prepare prompt for AI analysis
            prompt = self._create_analysis_prompt(file_path, content)
            
            # Call Ollama API
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": "gpt-oss:20b",  # Use gpt-oss:20b for code analysis
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Low temperature for consistent analysis
                        "top_p": 0.9
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get('response', '')
                
                # Parse AI response and extract insights
                return self._parse_ai_response(file_path, ai_response)
            
        except Exception as e:
            print(f"⚠️  AI analysis failed for {file_path.name}: {e}")
        
        return None
    
    def _create_analysis_prompt(self, file_path: Path, content: str) -> str:
        """Create a comprehensive prompt for AI code analysis"""
        return f"""You are an expert Python code reviewer. Analyze this code file and provide specific, actionable feedback.

File: {file_path.name}
Path: {file_path}

Code:
```python
{content[:2000]}  # Limit content to avoid token limits
```

Please provide a structured analysis with:
1. Code quality assessment (1-10 scale)
2. Specific issues found with line numbers if possible
3. Improvement suggestions
4. Security considerations
5. Performance optimization opportunities
6. Best practices recommendations

Format your response as JSON:
{{
    "quality_score": 8,
    "issues": ["list of specific issues"],
    "suggestions": ["list of improvement suggestions"],
    "security_notes": ["security considerations"],
    "performance_tips": ["performance optimization tips"],
    "best_practices": ["best practices recommendations"]
}}

Be specific and actionable. Focus on the most important issues first."""
    
    def _parse_ai_response(self, file_path: Path, ai_response: str) -> Dict[str, Any]:
        """Parse AI response and extract structured insights"""
        print(f"🔍 Parsing AI response for {file_path.name}")
        print(f"📝 Raw AI response: {ai_response[:200]}...")
        
        try:
            # Try to extract JSON from the response
            if '{' in ai_response and '}' in ai_response:
                start = ai_response.find('{')
                end = ai_response.rfind('}') + 1
                json_str = ai_response[start:end]
                
                print(f"🔍 Extracted JSON: {json_str}")
                analysis = json.loads(json_str)
                print(f"✅ Successfully parsed AI response for {file_path.name}")
                return {
                    'file': str(file_path),
                    'ai_analysis': analysis,
                    'raw_response': ai_response
                }
        except Exception as e:
            print(f"❌ JSON parsing failed for {file_path.name}: {e}")
        
        # Fallback: treat as unstructured text
        print(f"⚠️  Using fallback parsing for {file_path.name}")
        return {
            'file': str(file_path),
            'ai_analysis': {
                'quality_score': 0,
                'issues': ['Could not parse AI response'],
                'suggestions': ['Review AI response manually'],
                'security_notes': [],
                'performance_tips': [],
                'best_practices': []
            },
            'raw_response': ai_response
        }
    
    def _analyze_python_files(self, files: List[Path]):
        """Analyze Python files for common issues (static analysis)"""
        print(f"📝 Analyzing {len(files)} Python files...")
        
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse AST
                try:
                    tree = ast.parse(content)
                    self._analyze_ast(tree, file_path)
                except SyntaxError as e:
                    self.issues.append({
                        'file': str(file_path),
                        'type': 'syntax_error',
                        'line': e.lineno,
                        'message': f"Syntax error: {e.msg}"
                    })
                    
            except Exception as e:
                self.issues.append({
                    'file': str(file_path),
                    'type': 'read_error',
                    'message': f"Could not read file: {e}"
                })
    
    def _analyze_ast(self, tree: ast.AST, file_path: Path):
        """Analyze AST for code quality issues"""
        for node in ast.walk(tree):
            # Check for long functions (>50 lines)
            if isinstance(node, ast.FunctionDef):
                if hasattr(node, 'end_lineno') and hasattr(node, 'lineno'):
                    if node.end_lineno - node.lineno > 50:
                        self.suggestions.append({
                            'file': str(file_path),
                            'type': 'long_function',
                            'line': node.lineno,
                            'message': f"Function '{node.name}' is {node.end_lineno - node.lineno} lines long. Consider breaking it into smaller functions.",
                            'severity': 'warning'
                        })
            
            # Check for magic numbers
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                if isinstance(node.value, int) and abs(node.value) > 1000:
                    self.suggestions.append({
                        'file': str(file_path),
                        'type': 'magic_number',
                        'line': getattr(node, 'lineno', 'unknown'),
                        'message': f"Consider extracting magic number {node.value} into a named constant.",
                        'severity': 'info'
                    })
    
    def _check_common_issues(self):
        """Check for common development issues"""
        print("🔧 Checking for common issues...")
        
        # Get filtered Python files
        python_files = self._get_project_python_files()
        
        # Check for TODO comments
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        if 'TODO' in line.upper() or 'FIXME' in line.upper():
                            self.issues.append({
                                'file': str(file_path),
                                'type': 'todo_comment',
                                'line': line_num,
                                'message': f"TODO/FIXME comment found: {line.strip()}"
                            })
            except:
                continue
        
        # Check for large files
        for file_path in python_files:
            try:
                size = file_path.stat().st_size
                if size > 10000:  # 10KB
                    self.suggestions.append({
                        'file': str(file_path),
                        'type': 'large_file',
                        'line': 'N/A',
                        'message': f"File is {size} bytes. Consider splitting into smaller modules.",
                        'severity': 'warning'
                    })
            except:
                continue
    
    def _generate_ai_report(self) -> Dict[str, Any]:
        """Generate comprehensive AI-powered review report"""
        python_files = self._get_project_python_files()
        report = {
            'summary': {
                'total_files_analyzed': len(python_files),
                'files_analyzed_with_ai': len(self.ai_insights),
                'issues_found': len(self.issues),
                'suggestions_made': len(self.suggestions),
                'ai_insights_generated': len(self.ai_insights)
            },
            'issues': self.issues,
            'suggestions': self.suggestions,
            'ai_insights': self.ai_insights,
            'recommendations': self._generate_recommendations()
        }
        
        return report
    
    def _generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive review report (static analysis only)"""
        python_files = self._get_project_python_files()
        report = {
            'summary': {
                'total_files_analyzed': len(python_files),
                'issues_found': len(self.issues),
                'suggestions_made': len(self.suggestions)
            },
            'issues': self.issues,
            'suggestions': self.suggestions,
            'recommendations': self._generate_recommendations()
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if self.issues:
            recommendations.append("🔴 Address critical issues before proceeding")
        
        if len([s for s in self.suggestions if s['severity'] == 'warning']) > 5:
            recommendations.append("⚠️ Multiple warnings detected - consider code quality improvements")
        
        if len([s for s in self.suggestions if s['type'] == 'long_function']) > 0:
            recommendations.append("📏 Break down long functions for better maintainability")
        
        if len([s for s in self.suggestions if s['type'] == 'magic_number']) > 0:
            recommendations.append("🔢 Extract magic numbers into named constants")
        
        if self.ai_insights:
            recommendations.append("🤖 Review AI-generated insights for advanced recommendations")
            recommendations.append("🧠 AI analysis provides contextual, intelligent suggestions")
        
        if not recommendations:
            recommendations.append("✅ Code looks good! Keep up the good practices.")
        
        return recommendations

def main():
    parser = argparse.ArgumentParser(description="AI Code Review Tool with Ollama Integration")
    parser.add_argument("--path", default=".", help="Path to review")
    parser.add_argument("--rules", nargs="*", default=["all"], help="Rules to apply")
    parser.add_argument("--output", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--ollama-url", default="http://localhost:11434", help="Ollama API URL")
    
    args = parser.parse_args()
    
    # Run review
    reviewer = AICodeReviewer(args.path, args.rules, args.ollama_url)
    report = reviewer.run_review()
    
    # Output results
    if args.output == "json":
        print(json.dumps(report, indent=2))
    else:
        _print_text_report(report)

def _print_text_report(report: Dict[str, Any]):
    """Print human-readable report"""
    print("\n" + "="*60)
    print("🤖 AI CODE REVIEW REPORT (with Ollama Integration)")
    print("="*60)
    
    # Summary
    summary = report['summary']
    print(f"\n📊 SUMMARY:")
    print(f"  • Files analyzed: {summary['total_files_analyzed']}")
    if 'files_analyzed_with_ai' in summary:
        print(f"  • Files analyzed with AI: {summary['files_analyzed_with_ai']}")
    print(f"  • Issues found: {summary['issues_found']}")
    print(f"  • Suggestions made: {summary['suggestions_made']}")
    if 'ai_insights_generated' in summary:
        print(f"  • AI insights generated: {summary['ai_insights_generated']}")
    
    # AI Insights
    if 'ai_insights' in report and report['ai_insights']:
        print(f"\n🤖 AI INSIGHTS ({len(report['ai_insights'])}):")
        for insight in report['ai_insights']:
            print(f"  📁 {insight['file']}")
            ai_analysis = insight['ai_analysis']
            if 'quality_score' in ai_analysis:
                print(f"    Quality Score: {ai_analysis['quality_score']}/10")
            if 'issues' in ai_analysis and ai_analysis['issues']:
                print(f"    Issues: {', '.join(ai_analysis['issues'][:3])}")
            if 'suggestions' in ai_analysis and ai_analysis['suggestions']:
                print(f"    Suggestions: {', '.join(ai_analysis['suggestions'][:3])}")
            print()
    
    # Issues
    if report['issues']:
        print(f"\n🔴 ISSUES ({len(report['issues'])}):")
        for issue in report['issues']:
            print(f"  • {issue['file']}:{issue.get('line', 'N/A')} - {issue['message']}")
    
    # Suggestions
    if report['suggestions']:
        print(f"\n💡 SUGGESTIONS ({len(report['suggestions'])}):")
        for suggestion in report['suggestions']:
            severity_icon = "⚠️" if suggestion['severity'] == 'warning' else "ℹ️"
            print(f"  • {severity_icon} {suggestion['file']}:{suggestion.get('line', 'N/A')} - {suggestion['message']}")
    
    # Recommendations
    if report['recommendations']:
        print(f"\n🎯 RECOMMENDATIONS:")
        for rec in report['recommendations']:
            print(f"  • {rec}")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
