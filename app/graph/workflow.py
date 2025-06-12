from typing import Dict, Any, List, Tuple
from langgraph.graph import Graph, StateGraph
from app.agents.base_agent import AgentState
from app.agents.input_agent import InputAgent
from app.agents.component_identification_agent import ComponentIdentificationAgent
from app.agents.component_mapping_agent import ComponentMappingAgent
from app.agents.code_generation_agent import CodeGenerationAgent
from app.agents.code_modification_agent import CodeModificationAgent
from app.agents.output_agent import OutputAgent
from app.agents.static_component_mapping_agent import StaticComponentMappingAgent
from app.agents.detailed_code_generation_agent import DetailedCodeGenerationAgent
class WorkflowGraph:
    def __init__(self):
        # Initialize agents
        self.input_agent = InputAgent()
        self.component_identification_agent = ComponentIdentificationAgent()
        self.component_mapping_agent = ComponentMappingAgent()
        self.code_generation_agent = CodeGenerationAgent()
        self.code_modification_agent = CodeModificationAgent()
        self.output_agent = OutputAgent()
        self.static_component_mapping_agent = StaticComponentMappingAgent()
        self.detailed_code_generation_agent = DetailedCodeGenerationAgent()
        
        # Create the graph
        self.graph = self._create_graph()
    
    def _create_graph(self) -> Graph:
        # Create a new graph
        workflow = StateGraph(AgentState)
        
        # Add nodes for each agent
        workflow.add_node("input", self.input_agent.process)
        workflow.add_node("identify", self.component_identification_agent.process)
        # workflow.add_node("map", self.component_mapping_agent.process)
        # workflow.add_node("generate", self.code_generation_agent.process)
        workflow.add_node("static_map", self.static_component_mapping_agent.process)
        workflow.add_node("detailed_code_generation", self.detailed_code_generation_agent.process)
        # workflow.add_node("modify", self.code_modification_agent.process) 
        # workflow.add_node("output", self.output_agent.process)
        
        # Define the edges
        workflow.add_edge("input", "identify")
        workflow.add_edge("identify", "static_map")
        workflow.add_edge("static_map", "detailed_code_generation")
        # workflow.add_edge("static_map", "generate")
        # workflow.add_edge("generate", "modify")
        # workflow.add_edge("modify", "generate")
        
        # Define the edges for code modification
        # workflow.add_edge("output", "modify")
        # workflow.add_edge("modify", "output")
        
        # Set the entry point
        workflow.set_entry_point("input")
        
        # Set the finish point
        # workflow.set_finish_point("generate")
        return workflow.compile()
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the input data through the workflow
        """
        # Create initial state
        initial_state = AgentState(input_data=input_data)
        
        # Run the workflow
        final_state = await self.graph.ainvoke(initial_state)
        
        # Return the final output
        return final_state