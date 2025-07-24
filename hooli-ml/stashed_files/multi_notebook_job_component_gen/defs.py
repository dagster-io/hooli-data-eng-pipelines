"""
Component definitions for the multi notebook job component.
"""

import dagster as dg

# Load the component instance from the YAML configuration
defs = dg.load_component_from_yaml(dg.file_relative_path(__file__, "defs.yaml"))
