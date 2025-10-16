"""
MATLAB Engine service for model execution
"""

import os
import sys
import json
import asyncio
from typing import Dict, Any, Optional, List
import structlog
from pathlib import Path

try:
    import matlab.engine
    MATLAB_AVAILABLE = True
except ImportError:
    MATLAB_AVAILABLE = False
    matlab = None

from app.core.config import settings
from app.core.exceptions import MATLABException

logger = structlog.get_logger()


class MATLABService:
    """Service for MATLAB Engine integration"""
    
    def __init__(self):
        self.engine: Optional[Any] = None
        self.is_initialized = False
        self.matlab_path = settings.MATLAB_PATH
        
    async def initialize(self) -> bool:
        """Initialize MATLAB Engine"""
        if not MATLAB_AVAILABLE:
            raise MATLABException("MATLAB Engine for Python is not installed")
        
        try:
            # Start MATLAB engine
            self.engine = matlab.engine.start_matlab()
            
            # Add MATLAB path if specified
            if self.matlab_path and os.path.exists(self.matlab_path):
                self.engine.addpath(self.matlab_path)
            
            # Test MATLAB connection
            result = self.engine.eval("version")
            logger.info("MATLAB Engine initialized", version=result)
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            logger.error("Failed to initialize MATLAB Engine", error=str(e))
            raise MATLABException(f"MATLAB Engine initialization failed: {str(e)}")
    
    async def execute_model(
        self,
        model_path: str,
        input_data: Dict[str, Any],
        startup_script: Optional[str] = None,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """
        Execute a MATLAB/Simulink model with input data
        
        Args:
            model_path: Path to the model file (.slx or .m)
            input_data: Input data for the model
            startup_script: Optional startup script to run before model execution
            timeout: Execution timeout in seconds
            
        Returns:
            Dictionary containing output data and execution metadata
        """
        if not self.is_initialized:
            await self.initialize()
        
        try:
            # Change to model directory
            model_dir = os.path.dirname(model_path)
            model_name = os.path.basename(model_path)
            
            if model_dir:
                self.engine.cd(model_dir)
            
            # Run startup script if provided
            if startup_script:
                await self._run_startup_script(startup_script)
            
            # Execute model based on file type
            if model_name.endswith('.slx'):
                result = await self._execute_simulink_model(model_name, input_data, timeout)
            elif model_name.endswith('.m'):
                result = await self._execute_m_file(model_name, input_data, timeout)
            else:
                raise MATLABException(f"Unsupported model file type: {model_name}")
            
            logger.info("Model execution completed", model=model_name, success=True)
            return result
            
        except Exception as e:
            logger.error("Model execution failed", model=model_path, error=str(e))
            raise MATLABException(f"Model execution failed: {str(e)}")
    
    async def _run_startup_script(self, script_path: str):
        """Run startup script"""
        try:
            if os.path.exists(script_path):
                script_name = os.path.basename(script_path).replace('.m', '')
                self.engine.eval(f"run('{script_name}')")
                logger.info("Startup script executed", script=script_path)
        except Exception as e:
            logger.warning("Startup script execution failed", script=script_path, error=str(e))
    
    async def _execute_simulink_model(
        self,
        model_name: str,
        input_data: Dict[str, Any],
        timeout: int
    ) -> Dict[str, Any]:
        """Execute Simulink model"""
        try:
            # Load model
            model_name_without_ext = model_name.replace('.slx', '')
            self.engine.eval(f"load_system('{model_name_without_ext}')")
            
            # Set input parameters
            for param_name, param_value in input_data.items():
                if isinstance(param_value, (int, float)):
                    self.engine.eval(f"set_param('{model_name_without_ext}/{param_name}', 'Value', '{param_value}')")
                elif isinstance(param_value, str):
                    self.engine.eval(f"set_param('{model_name_without_ext}/{param_name}', 'Value', '{param_value}')")
            
            # Run simulation
            self.engine.eval(f"sim('{model_name_without_ext}')")
            
            # Extract output data
            output_data = {}
            try:
                # Try to get common output variables
                output_vars = ['y', 'out', 'simout', 'output']
                for var in output_vars:
                    try:
                        if self.engine.eval(f"exist('{var}', 'var')"):
                            output_data[var] = self.engine.workspace[var]
                    except:
                        continue
            except Exception as e:
                logger.warning("Could not extract output data", error=str(e))
            
            # Close model
            self.engine.eval(f"close_system('{model_name_without_ext}')")
            
            return {
                "output_data": output_data,
                "execution_time": 0,  # TODO: Measure actual execution time
                "status": "success"
            }
            
        except Exception as e:
            # Ensure model is closed even if execution fails
            try:
                model_name_without_ext = model_name.replace('.slx', '')
                self.engine.eval(f"close_system('{model_name_without_ext}')")
            except:
                pass
            raise e
    
    async def _execute_m_file(
        self,
        file_name: str,
        input_data: Dict[str, Any],
        timeout: int
    ) -> Dict[str, Any]:
        """Execute MATLAB M-file"""
        try:
            # Set input variables in MATLAB workspace
            for var_name, var_value in input_data.items():
                if isinstance(var_value, (int, float)):
                    self.engine.workspace[var_name] = matlab.double([var_value])
                elif isinstance(var_value, list):
                    self.engine.workspace[var_name] = matlab.double(var_value)
                elif isinstance(var_value, str):
                    self.engine.workspace[var_name] = var_value
            
            # Execute the M-file
            file_name_without_ext = file_name.replace('.m', '')
            self.engine.eval(f"run('{file_name_without_ext}')")
            
            # Extract output data
            output_data = {}
            try:
                # Get all variables from workspace
                workspace_vars = self.engine.eval("who")
                for var in workspace_vars:
                    if var not in input_data:  # Only get output variables
                        try:
                            output_data[var] = self.engine.workspace[var]
                        except:
                            continue
            except Exception as e:
                logger.warning("Could not extract output data", error=str(e))
            
            return {
                "output_data": output_data,
                "execution_time": 0,  # TODO: Measure actual execution time
                "status": "success"
            }
            
        except Exception as e:
            raise e
    
    async def get_model_info(self, model_path: str) -> Dict[str, Any]:
        """Get information about a MATLAB/Simulink model"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            model_info = {
                "path": model_path,
                "name": os.path.basename(model_path),
                "type": "unknown",
                "parameters": [],
                "outputs": []
            }
            
            if model_path.endswith('.slx'):
                model_info["type"] = "simulink"
                # TODO: Extract Simulink model parameters and outputs
            elif model_path.endswith('.m'):
                model_info["type"] = "matlab"
                # TODO: Parse M-file to extract parameters and outputs
            
            return model_info
            
        except Exception as e:
            logger.error("Failed to get model info", model=model_path, error=str(e))
            raise MATLABException(f"Failed to get model info: {str(e)}")
    
    async def validate_model(self, model_path: str) -> bool:
        """Validate if a model can be executed"""
        try:
            if not os.path.exists(model_path):
                return False
            
            # Check file extension
            if not model_path.endswith(('.slx', '.m')):
                return False
            
            # TODO: Add more validation logic
            return True
            
        except Exception as e:
            logger.error("Model validation failed", model=model_path, error=str(e))
            return False
    
    def cleanup(self):
        """Cleanup MATLAB Engine"""
        if self.engine:
            try:
                self.engine.quit()
                logger.info("MATLAB Engine cleaned up")
            except Exception as e:
                logger.warning("Error during MATLAB Engine cleanup", error=str(e))
            finally:
                self.engine = None
                self.is_initialized = False
