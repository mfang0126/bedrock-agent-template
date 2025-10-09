"""
Test Suite Runner for Coding Agent

Provides comprehensive test execution with framework detection, result parsing,
and detailed reporting for various testing frameworks.
"""

import os
import re
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Tuple
import logging
from datetime import datetime
from .command_executor import CommandExecutor

logger = logging.getLogger(__name__)


class TestRunnerError(Exception):
    """Raised when test runner operations fail"""
    pass


class TestResult:
    """Represents a single test result"""
    
    def __init__(self, name: str, status: str, duration: float = 0.0,
                 message: str = '', file_path: str = '', line_number: int = 0):
        self.name = name
        self.status = status  # passed, failed, skipped, error
        self.duration = duration
        self.message = message
        self.file_path = file_path
        self.line_number = line_number
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'status': self.status,
            'duration': self.duration,
            'message': self.message,
            'file_path': self.file_path,
            'line_number': self.line_number
        }


class TestSuite:
    """Represents a test suite with multiple test results"""
    
    def __init__(self, name: str, framework: str):
        self.name = name
        self.framework = framework
        self.tests: List[TestResult] = []
        self.duration = 0.0
        self.start_time = datetime.now()
        self.end_time = None
    
    def add_test(self, test: TestResult):
        self.tests.append(test)
        self.duration += test.duration
    
    def finish(self):
        self.end_time = datetime.now()
    
    @property
    def total_tests(self) -> int:
        return len(self.tests)
    
    @property
    def passed_tests(self) -> int:
        return len([t for t in self.tests if t.status == 'passed'])
    
    @property
    def failed_tests(self) -> int:
        return len([t for t in self.tests if t.status == 'failed'])
    
    @property
    def skipped_tests(self) -> int:
        return len([t for t in self.tests if t.status == 'skipped'])
    
    @property
    def error_tests(self) -> int:
        return len([t for t in self.tests if t.status == 'error'])
    
    @property
    def success_rate(self) -> float:
        if self.total_tests == 0:
            return 0.0
        return (self.passed_tests / self.total_tests) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'framework': self.framework,
            'total_tests': self.total_tests,
            'passed_tests': self.passed_tests,
            'failed_tests': self.failed_tests,
            'skipped_tests': self.skipped_tests,
            'error_tests': self.error_tests,
            'success_rate': self.success_rate,
            'duration': self.duration,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'tests': [test.to_dict() for test in self.tests]
        }


class TestRunner:
    """
    Comprehensive test runner with framework detection and result parsing
    """
    
    def __init__(self, workspace_root: str):
        """
        Initialize test runner with workspace root
        
        Args:
            workspace_root: Root directory for test execution
        """
        self.workspace_root = Path(workspace_root).resolve()
        self.command_executor = CommandExecutor(str(workspace_root))
        
        # Framework detection patterns
        self.framework_patterns = {
            'pytest': {
                'files': ['pytest.ini', 'pyproject.toml', 'setup.cfg', 'tox.ini'],
                'directories': ['tests', 'test'],
                'file_patterns': ['test_*.py', '*_test.py'],
                'imports': ['pytest', 'import pytest']
            },
            'unittest': {
                'files': [],
                'directories': ['tests', 'test'],
                'file_patterns': ['test_*.py', '*_test.py'],
                'imports': ['unittest', 'from unittest']
            },
            'jest': {
                'files': ['jest.config.js', 'jest.config.json', 'package.json'],
                'directories': ['__tests__', 'tests', 'test'],
                'file_patterns': ['*.test.js', '*.spec.js', '*.test.ts', '*.spec.ts'],
                'imports': ['jest', 'describe(', 'it(', 'test(']
            },
            'mocha': {
                'files': ['mocha.opts', '.mocharc.json', '.mocharc.yml'],
                'directories': ['test', 'tests'],
                'file_patterns': ['*.test.js', '*.spec.js'],
                'imports': ['mocha', 'describe(', 'it(']
            },
            'junit': {
                'files': ['pom.xml', 'build.gradle'],
                'directories': ['src/test/java'],
                'file_patterns': ['*Test.java', '*Tests.java'],
                'imports': ['@Test', 'org.junit']
            },
            'testng': {
                'files': ['testng.xml'],
                'directories': ['src/test/java'],
                'file_patterns': ['*Test.java', '*Tests.java'],
                'imports': ['@Test', 'org.testng']
            },
            'gtest': {
                'files': ['CMakeLists.txt'],
                'directories': ['tests', 'test'],
                'file_patterns': ['*_test.cpp', '*_test.cc', 'test_*.cpp'],
                'imports': ['#include <gtest/gtest.h>', 'TEST(', 'TEST_F(']
            },
            'rspec': {
                'files': ['.rspec', 'spec_helper.rb'],
                'directories': ['spec'],
                'file_patterns': ['*_spec.rb'],
                'imports': ['require \'rspec\'', 'describe ', 'it ']
            }
        }
    
    def detect_frameworks(self, directory: str = '') -> List[str]:
        """
        Detect testing frameworks in the workspace
        
        Args:
            directory: Directory to scan (relative to workspace)
            
        Returns:
            List of detected framework names
        """
        try:
            if directory:
                scan_dir = self.workspace_root / directory
            else:
                scan_dir = self.workspace_root
            
            detected_frameworks = []
            
            for framework, patterns in self.framework_patterns.items():
                framework_detected = False
                
                # Check for framework-specific files
                for file_pattern in patterns['files']:
                    if list(scan_dir.glob(file_pattern)):
                        framework_detected = True
                        break
                
                # Check for framework-specific directories
                if not framework_detected:
                    for dir_pattern in patterns['directories']:
                        if (scan_dir / dir_pattern).exists():
                            framework_detected = True
                            break
                
                # Check for test files with framework patterns
                if not framework_detected:
                    for file_pattern in patterns['file_patterns']:
                        test_files = list(scan_dir.rglob(file_pattern))
                        if test_files:
                            # Check file contents for framework imports
                            for test_file in test_files[:5]:  # Check first 5 files
                                try:
                                    content = test_file.read_text(encoding='utf-8')
                                    for import_pattern in patterns['imports']:
                                        if import_pattern in content:
                                            framework_detected = True
                                            break
                                    if framework_detected:
                                        break
                                except:
                                    continue
                
                if framework_detected:
                    detected_frameworks.append(framework)
            
            return detected_frameworks
            
        except Exception as e:
            logger.error(f"Failed to detect frameworks: {e}")
            return []
    
    def find_test_files(self, framework: str, directory: str = '') -> List[str]:
        """
        Find test files for a specific framework
        
        Args:
            framework: Framework name
            directory: Directory to search (relative to workspace)
            
        Returns:
            List of test file paths
        """
        try:
            if directory:
                search_dir = self.workspace_root / directory
            else:
                search_dir = self.workspace_root
            
            if framework not in self.framework_patterns:
                return []
            
            patterns = self.framework_patterns[framework]
            test_files = []
            
            # Search for test files using patterns
            for file_pattern in patterns['file_patterns']:
                files = list(search_dir.rglob(file_pattern))
                for file_path in files:
                    try:
                        relative_path = file_path.relative_to(self.workspace_root)
                        test_files.append(str(relative_path))
                    except ValueError:
                        continue
            
            return sorted(test_files)
            
        except Exception as e:
            logger.error(f"Failed to find test files for {framework}: {e}")
            return []
    
    def run_tests(self, framework: str = None, test_path: str = '',
                  timeout: int = 600, verbose: bool = True) -> Dict[str, Any]:
        """
        Run tests using detected or specified framework
        
        Args:
            framework: Framework to use (auto-detect if None)
            test_path: Specific test path to run
            timeout: Test execution timeout
            verbose: Enable verbose output
            
        Returns:
            Dictionary with test results
        """
        try:
            # Auto-detect framework if not specified
            if not framework:
                detected = self.detect_frameworks()
                if not detected:
                    return {
                        'success': False,
                        'error': 'No testing framework detected',
                        'detected_frameworks': []
                    }
                framework = detected[0]  # Use first detected framework
            
            # Run tests based on framework
            if framework == 'pytest':
                return self._run_pytest(test_path, timeout, verbose)
            elif framework == 'unittest':
                return self._run_unittest(test_path, timeout, verbose)
            elif framework == 'jest':
                return self._run_jest(test_path, timeout, verbose)
            elif framework == 'mocha':
                return self._run_mocha(test_path, timeout, verbose)
            elif framework == 'junit':
                return self._run_junit(test_path, timeout, verbose)
            elif framework == 'gtest':
                return self._run_gtest(test_path, timeout, verbose)
            elif framework == 'rspec':
                return self._run_rspec(test_path, timeout, verbose)
            else:
                return {
                    'success': False,
                    'error': f'Framework {framework} not supported',
                    'framework': framework
                }
                
        except Exception as e:
            logger.error(f"Failed to run tests: {e}")
            return {
                'success': False,
                'error': str(e),
                'framework': framework
            }
    
    def _run_pytest(self, test_path: str, timeout: int, verbose: bool) -> Dict[str, Any]:
        """Run pytest tests"""
        cmd_parts = ['python', '-m', 'pytest']
        
        if verbose:
            cmd_parts.append('-v')
        
        # Add JSON report for parsing
        cmd_parts.extend(['--tb=short', '--json-report', '--json-report-file=test_results.json'])
        
        if test_path:
            cmd_parts.append(test_path)
        
        command = ' '.join(cmd_parts)
        result = self.command_executor.execute_command(command, timeout=timeout)
        
        # Parse results
        test_suite = TestSuite('pytest', 'pytest')
        
        # Try to parse JSON report
        json_report_path = self.workspace_root / 'test_results.json'
        if json_report_path.exists():
            try:
                with open(json_report_path, 'r') as f:
                    json_data = json.load(f)
                
                for test in json_data.get('tests', []):
                    test_result = TestResult(
                        name=test.get('nodeid', ''),
                        status='passed' if test.get('outcome') == 'passed' else 'failed',
                        duration=test.get('duration', 0.0),
                        message=test.get('call', {}).get('longrepr', ''),
                        file_path=test.get('file', ''),
                        line_number=test.get('lineno', 0)
                    )
                    test_suite.add_test(test_result)
                
                # Clean up report file
                json_report_path.unlink()
                
            except Exception as e:
                logger.warning(f"Failed to parse pytest JSON report: {e}")
        
        # Fallback to stdout parsing if JSON parsing failed
        if not test_suite.tests:
            test_suite = self._parse_pytest_output(result.get('stdout', ''))
        
        test_suite.finish()
        
        return {
            'success': result['success'],
            'framework': 'pytest',
            'command': command,
            'raw_output': result.get('stdout', ''),
            'error_output': result.get('stderr', ''),
            'duration': result.get('duration', 0),
            'test_suite': test_suite.to_dict()
        }
    
    def _run_unittest(self, test_path: str, timeout: int, verbose: bool) -> Dict[str, Any]:
        """Run unittest tests"""
        cmd_parts = ['python', '-m', 'unittest']
        
        if verbose:
            cmd_parts.append('-v')
        
        if test_path:
            cmd_parts.append(test_path)
        else:
            cmd_parts.append('discover')
        
        command = ' '.join(cmd_parts)
        result = self.command_executor.execute_command(command, timeout=timeout)
        
        # Parse results from stdout
        test_suite = self._parse_unittest_output(result.get('stdout', ''))
        test_suite.finish()
        
        return {
            'success': result['success'],
            'framework': 'unittest',
            'command': command,
            'raw_output': result.get('stdout', ''),
            'error_output': result.get('stderr', ''),
            'duration': result.get('duration', 0),
            'test_suite': test_suite.to_dict()
        }
    
    def _run_jest(self, test_path: str, timeout: int, verbose: bool) -> Dict[str, Any]:
        """Run Jest tests"""
        cmd_parts = ['npx', 'jest']
        
        if verbose:
            cmd_parts.append('--verbose')
        
        # Add JSON output for parsing
        cmd_parts.extend(['--json', '--outputFile=test_results.json'])
        
        if test_path:
            cmd_parts.append(test_path)
        
        command = ' '.join(cmd_parts)
        result = self.command_executor.execute_command(command, timeout=timeout)
        
        # Parse JSON results
        test_suite = TestSuite('jest', 'jest')
        
        json_report_path = self.workspace_root / 'test_results.json'
        if json_report_path.exists():
            try:
                with open(json_report_path, 'r') as f:
                    json_data = json.load(f)
                
                for test_result in json_data.get('testResults', []):
                    for assertion in test_result.get('assertionResults', []):
                        test = TestResult(
                            name=assertion.get('fullName', ''),
                            status='passed' if assertion.get('status') == 'passed' else 'failed',
                            duration=assertion.get('duration', 0.0) / 1000,  # Convert ms to seconds
                            message=assertion.get('failureMessages', [''])[0] if assertion.get('failureMessages') else '',
                            file_path=test_result.get('name', '')
                        )
                        test_suite.add_test(test)
                
                json_report_path.unlink()
                
            except Exception as e:
                logger.warning(f"Failed to parse Jest JSON report: {e}")
        
        test_suite.finish()
        
        return {
            'success': result['success'],
            'framework': 'jest',
            'command': command,
            'raw_output': result.get('stdout', ''),
            'error_output': result.get('stderr', ''),
            'duration': result.get('duration', 0),
            'test_suite': test_suite.to_dict()
        }
    
    def _run_mocha(self, test_path: str, timeout: int, verbose: bool) -> Dict[str, Any]:
        """Run Mocha tests"""
        cmd_parts = ['npx', 'mocha']
        
        # Add JSON reporter
        cmd_parts.extend(['--reporter', 'json'])
        
        if test_path:
            cmd_parts.append(test_path)
        
        command = ' '.join(cmd_parts)
        result = self.command_executor.execute_command(command, timeout=timeout)
        
        # Parse JSON output
        test_suite = self._parse_mocha_json_output(result.get('stdout', ''))
        test_suite.finish()
        
        return {
            'success': result['success'],
            'framework': 'mocha',
            'command': command,
            'raw_output': result.get('stdout', ''),
            'error_output': result.get('stderr', ''),
            'duration': result.get('duration', 0),
            'test_suite': test_suite.to_dict()
        }
    
    def _run_junit(self, test_path: str, timeout: int, verbose: bool) -> Dict[str, Any]:
        """Run JUnit tests"""
        # Check if Maven or Gradle project
        if (self.workspace_root / 'pom.xml').exists():
            command = 'mvn test'
        elif (self.workspace_root / 'build.gradle').exists():
            command = './gradlew test'
        else:
            return {
                'success': False,
                'error': 'No Maven or Gradle build file found',
                'framework': 'junit'
            }
        
        result = self.command_executor.execute_command(command, timeout=timeout)
        
        # Parse XML test reports
        test_suite = self._parse_junit_xml_reports()
        test_suite.finish()
        
        return {
            'success': result['success'],
            'framework': 'junit',
            'command': command,
            'raw_output': result.get('stdout', ''),
            'error_output': result.get('stderr', ''),
            'duration': result.get('duration', 0),
            'test_suite': test_suite.to_dict()
        }
    
    def _run_gtest(self, test_path: str, timeout: int, verbose: bool) -> Dict[str, Any]:
        """Run Google Test tests"""
        # Build and run tests
        build_cmd = 'cmake . && make'
        build_result = self.command_executor.execute_command(build_cmd, timeout=timeout//2)
        
        if not build_result['success']:
            return {
                'success': False,
                'error': 'Failed to build tests',
                'framework': 'gtest',
                'build_output': build_result.get('stdout', ''),
                'build_error': build_result.get('stderr', '')
            }
        
        # Find test executable
        test_executables = list(self.workspace_root.glob('*test*'))
        if not test_executables:
            return {
                'success': False,
                'error': 'No test executable found',
                'framework': 'gtest'
            }
        
        # Run tests with XML output
        test_cmd = f'./{test_executables[0].name} --gtest_output=xml:test_results.xml'
        result = self.command_executor.execute_command(test_cmd, timeout=timeout//2)
        
        # Parse XML results
        test_suite = self._parse_gtest_xml_output()
        test_suite.finish()
        
        return {
            'success': result['success'],
            'framework': 'gtest',
            'command': test_cmd,
            'raw_output': result.get('stdout', ''),
            'error_output': result.get('stderr', ''),
            'duration': result.get('duration', 0),
            'test_suite': test_suite.to_dict()
        }
    
    def _run_rspec(self, test_path: str, timeout: int, verbose: bool) -> Dict[str, Any]:
        """Run RSpec tests"""
        cmd_parts = ['rspec']
        
        # Add JSON formatter
        cmd_parts.extend(['--format', 'json', '--out', 'test_results.json'])
        
        if verbose:
            cmd_parts.extend(['--format', 'documentation'])
        
        if test_path:
            cmd_parts.append(test_path)
        
        command = ' '.join(cmd_parts)
        result = self.command_executor.execute_command(command, timeout=timeout)
        
        # Parse JSON results
        test_suite = TestSuite('rspec', 'rspec')
        
        json_report_path = self.workspace_root / 'test_results.json'
        if json_report_path.exists():
            try:
                with open(json_report_path, 'r') as f:
                    json_data = json.load(f)
                
                for example in json_data.get('examples', []):
                    test = TestResult(
                        name=example.get('full_description', ''),
                        status=example.get('status', ''),
                        duration=example.get('run_time', 0.0),
                        message=example.get('exception', {}).get('message', '') if example.get('exception') else '',
                        file_path=example.get('file_path', ''),
                        line_number=example.get('line_number', 0)
                    )
                    test_suite.add_test(test)
                
                json_report_path.unlink()
                
            except Exception as e:
                logger.warning(f"Failed to parse RSpec JSON report: {e}")
        
        test_suite.finish()
        
        return {
            'success': result['success'],
            'framework': 'rspec',
            'command': command,
            'raw_output': result.get('stdout', ''),
            'error_output': result.get('stderr', ''),
            'duration': result.get('duration', 0),
            'test_suite': test_suite.to_dict()
        }
    
    def _parse_pytest_output(self, output: str) -> TestSuite:
        """Parse pytest stdout output"""
        test_suite = TestSuite('pytest-fallback', 'pytest')
        
        # Parse test results from output
        lines = output.split('\n')
        for line in lines:
            if '::' in line and ('PASSED' in line or 'FAILED' in line or 'SKIPPED' in line):
                parts = line.split()
                if len(parts) >= 2:
                    test_name = parts[0]
                    status = 'passed' if 'PASSED' in line else 'failed' if 'FAILED' in line else 'skipped'
                    test = TestResult(name=test_name, status=status)
                    test_suite.add_test(test)
        
        return test_suite
    
    def _parse_unittest_output(self, output: str) -> TestSuite:
        """Parse unittest stdout output"""
        test_suite = TestSuite('unittest', 'unittest')
        
        # Parse test results from output
        lines = output.split('\n')
        for line in lines:
            if ' ... ' in line:
                parts = line.split(' ... ')
                if len(parts) == 2:
                    test_name = parts[0].strip()
                    status_text = parts[1].strip()
                    status = 'passed' if status_text == 'ok' else 'failed' if status_text in ['FAIL', 'ERROR'] else 'skipped'
                    test = TestResult(name=test_name, status=status)
                    test_suite.add_test(test)
        
        return test_suite
    
    def _parse_mocha_json_output(self, output: str) -> TestSuite:
        """Parse Mocha JSON output"""
        test_suite = TestSuite('mocha', 'mocha')
        
        try:
            json_data = json.loads(output)
            for test in json_data.get('tests', []):
                test_result = TestResult(
                    name=test.get('fullTitle', ''),
                    status='passed' if test.get('state') == 'passed' else 'failed',
                    duration=test.get('duration', 0.0) / 1000,  # Convert ms to seconds
                    message=test.get('err', {}).get('message', '') if test.get('err') else ''
                )
                test_suite.add_test(test_result)
        except json.JSONDecodeError:
            logger.warning("Failed to parse Mocha JSON output")
        
        return test_suite
    
    def _parse_junit_xml_reports(self) -> TestSuite:
        """Parse JUnit XML test reports"""
        test_suite = TestSuite('junit', 'junit')
        
        # Look for XML reports in common locations
        report_paths = [
            self.workspace_root / 'target' / 'surefire-reports',
            self.workspace_root / 'build' / 'test-results' / 'test'
        ]
        
        for report_dir in report_paths:
            if report_dir.exists():
                for xml_file in report_dir.glob('TEST-*.xml'):
                    try:
                        tree = ET.parse(xml_file)
                        root = tree.getroot()
                        
                        for testcase in root.findall('testcase'):
                            name = testcase.get('name', '')
                            classname = testcase.get('classname', '')
                            duration = float(testcase.get('time', 0))
                            
                            # Check for failure or error
                            failure = testcase.find('failure')
                            error = testcase.find('error')
                            skipped = testcase.find('skipped')
                            
                            if failure is not None:
                                status = 'failed'
                                message = failure.get('message', '')
                            elif error is not None:
                                status = 'error'
                                message = error.get('message', '')
                            elif skipped is not None:
                                status = 'skipped'
                                message = skipped.get('message', '')
                            else:
                                status = 'passed'
                                message = ''
                            
                            test = TestResult(
                                name=f"{classname}.{name}",
                                status=status,
                                duration=duration,
                                message=message
                            )
                            test_suite.add_test(test)
                            
                    except ET.ParseError as e:
                        logger.warning(f"Failed to parse XML report {xml_file}: {e}")
        
        return test_suite
    
    def _parse_gtest_xml_output(self) -> TestSuite:
        """Parse Google Test XML output"""
        test_suite = TestSuite('gtest', 'gtest')
        
        xml_file = self.workspace_root / 'test_results.xml'
        if xml_file.exists():
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()
                
                for testcase in root.findall('.//testcase'):
                    name = testcase.get('name', '')
                    classname = testcase.get('classname', '')
                    duration = float(testcase.get('time', 0))
                    
                    failure = testcase.find('failure')
                    if failure is not None:
                        status = 'failed'
                        message = failure.get('message', '')
                    else:
                        status = 'passed'
                        message = ''
                    
                    test = TestResult(
                        name=f"{classname}.{name}",
                        status=status,
                        duration=duration,
                        message=message
                    )
                    test_suite.add_test(test)
                
                xml_file.unlink()  # Clean up
                
            except ET.ParseError as e:
                logger.warning(f"Failed to parse GTest XML output: {e}")
        
        return test_suite
    
    def get_test_coverage(self, framework: str = None) -> Dict[str, Any]:
        """
        Get test coverage information
        
        Args:
            framework: Framework to use for coverage
            
        Returns:
            Dictionary with coverage information
        """
        try:
            if not framework:
                detected = self.detect_frameworks()
                if not detected:
                    return {
                        'success': False,
                        'error': 'No testing framework detected'
                    }
                framework = detected[0]
            
            if framework == 'pytest':
                command = 'python -m pytest --cov=. --cov-report=json'
            elif framework == 'jest':
                command = 'npx jest --coverage --coverageReporters=json'
            else:
                return {
                    'success': False,
                    'error': f'Coverage not supported for {framework}',
                    'framework': framework
                }
            
            result = self.command_executor.execute_command(command, timeout=600)
            
            # Parse coverage report
            coverage_data = {}
            if framework == 'pytest':
                coverage_file = self.workspace_root / 'coverage.json'
            else:  # jest
                coverage_file = self.workspace_root / 'coverage' / 'coverage-final.json'
            
            if coverage_file.exists():
                try:
                    with open(coverage_file, 'r') as f:
                        coverage_data = json.load(f)
                except json.JSONDecodeError:
                    pass
            
            return {
                'success': result['success'],
                'framework': framework,
                'command': command,
                'coverage_data': coverage_data,
                'raw_output': result.get('stdout', ''),
                'error_output': result.get('stderr', '')
            }
            
        except Exception as e:
            logger.error(f"Failed to get test coverage: {e}")
            return {
                'success': False,
                'error': str(e),
                'framework': framework
            }