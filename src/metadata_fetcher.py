"""
Targetprocess entity metadata fetcher
Gets real field names, states, and relationships from TP API
"""
import requests
import logging
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TargetprocessMetadata:
    def __init__(self, domain: str, token: str):
        """
        Initialize TP metadata fetcher
        Args:
            domain: Your TP domain (e.g., "company.tpondemand.com")
            token: Your TP access token
        """
        self.domain = domain.rstrip('/')
        self.token = token
        self.base_url = f"https://{self.domain}/api/v1"
        self.metadata_cache = {}
        
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make API request to Targetprocess"""
        try:
            url = f"{self.base_url}/{endpoint}"
            
            # Add token to params
            if params is None:
                params = {}
            params['access_token'] = self.token
            params['format'] = 'json'
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return None
    
    def get_entity_metadata(self, entity_type: str) -> Dict[str, Any]:
        """
        Get comprehensive metadata for an entity type
        """
        # Use cache if available
        cache_key = f"metadata_{entity_type.lower()}"
        if cache_key in self.metadata_cache:
            return self.metadata_cache[cache_key]
        
        logger.info(f"Fetching metadata for {entity_type}")
        
        # Get sample entities to understand structure
        entities = self._make_request(f"{entity_type}s", {"take": 25, "include": "[CustomFields,EntityState,Project]"})
        
        if not entities or 'Items' not in entities:
            logger.error(f"Failed to fetch {entity_type} data")
            return self._get_default_metadata(entity_type)
        
        # Extract metadata from sample entities
        metadata = self._extract_metadata_from_entities(entities['Items'], entity_type)
        
        # Cache the result
        self.metadata_cache[cache_key] = metadata
        
        return metadata
    
    def _extract_metadata_from_entities(self, entities: List[Dict], entity_type: str) -> Dict[str, Any]:
        """Extract metadata from actual entity records"""
        metadata = {
            "entity_type": entity_type,
            "standard_fields": set(),
            "custom_fields": set(),
            "states": set(),
            "relationships": set(),
            "sample_data": {}
        }
        
        for entity in entities:
            # Extract standard fields
            for field_name, field_value in entity.items():
                if field_name not in ['ResourceType', 'CustomFields']:
                    metadata["standard_fields"].add(field_name)
                    
                    # Collect sample values for important fields
                    if field_name in ['EntityState', 'Project'] and field_value:
                        if isinstance(field_value, dict) and 'Name' in field_value:
                            if field_name == 'EntityState':
                                metadata["states"].add(field_value['Name'])
                            elif field_name == 'Project':
                                metadata["relationships"].add(f"Project: {field_value['Name']}")
            
            # Extract custom fields
            if 'CustomFields' in entity and entity['CustomFields']:
                for cf in entity['CustomFields']:
                    if 'Name' in cf:
                        metadata["custom_fields"].add(cf['Name'])
        
        # Convert sets to sorted lists for JSON serialization
        metadata["standard_fields"] = sorted(list(metadata["standard_fields"]))
        metadata["custom_fields"] = sorted(list(metadata["custom_fields"]))
        metadata["states"] = sorted(list(metadata["states"]))
        metadata["relationships"] = sorted(list(metadata["relationships"]))
        
        # Get process states if we have EntityState info
        if metadata["states"]:
            process_states = self._get_process_states(entity_type)
            if process_states:
                metadata["process_states"] = process_states
        
        logger.info(f"Extracted metadata for {entity_type}: {len(metadata['standard_fields'])} standard fields, {len(metadata['custom_fields'])} custom fields")
        
        return metadata
    
    def _get_process_states(self, entity_type: str) -> List[Dict]:
        """Get detailed state information from processes"""
        try:
            processes = self._make_request("Processes", {
                "take": 50,
                "include": "[EntityStates[EntityType,Name,IsInitial,IsPlanned,IsFinal]]",
                "where": f"EntityStates.EntityType.Name=='{entity_type}'"
            })
            
            if not processes or 'Items' not in processes:
                return []
            
            states = []
            for process in processes['Items']:
                if 'EntityStates' in process:
                    for state in process['EntityStates']:
                        if state.get('EntityType', {}).get('Name') == entity_type:
                            states.append({
                                'id': state.get('Id'),
                                'name': state.get('Name'),
                                'isInitial': state.get('IsInitial', False),
                                'isPlanned': state.get('IsPlanned', False),
                                'isFinal': state.get('IsFinal', False)
                            })
            
            return states
            
        except Exception as e:
            logger.error(f"Failed to get process states: {e}")
            return []
    
    def _get_default_metadata(self, entity_type: str) -> Dict[str, Any]:
        """Return default metadata when API fails"""
        defaults = {
            "UserStory": {
                "standard_fields": ["Id", "Name", "Description", "EntityState", "Project", "TimeSpent", "Effort"],
                "custom_fields": [],
                "states": ["New", "Planned", "In Progress", "Done"],
                "relationships": ["Project", "Feature", "Tasks", "Bugs"]
            },
            "Bug": {
                "standard_fields": ["Id", "Name", "Description", "EntityState", "Project", "TimeSpent", "Severity"],
                "custom_fields": [],
                "states": ["Open", "In Progress", "Fixed", "Closed"],
                "relationships": ["Project", "UserStory", "Release"]
            },
            "Task": {
                "standard_fields": ["Id", "Name", "Description", "EntityState", "Project", "TimeSpent", "Effort"],
                "custom_fields": [],
                "states": ["Open", "In Progress", "Done"],
                "relationships": ["Project", "UserStory"]
            }
        }
        
        return {
            "entity_type": entity_type,
            "source": "default",
            **defaults.get(entity_type, defaults["UserStory"])
        }
    
    def get_field_suggestions(self, entity_type: str, field_partial: str = "") -> List[str]:
        """Get field name suggestions for autocomplete"""
        metadata = self.get_entity_metadata(entity_type)
        
        all_fields = metadata["standard_fields"] + metadata["custom_fields"]
        
        if field_partial:
            # Filter fields that contain the partial string
            suggestions = [f for f in all_fields if field_partial.lower() in f.lower()]
        else:
            suggestions = all_fields
        
        return sorted(suggestions)
    
    def validate_field_access(self, entity_type: str, field_name: str) -> Dict[str, Any]:
        """Validate how a field should be accessed in JavaScript"""
        metadata = self.get_entity_metadata(entity_type)
        
        result = {
            "field_name": field_name,
            "exists": False,
            "access_pattern": None,
            "field_type": "unknown"
        }
        
        if field_name in metadata["standard_fields"]:
            result["exists"] = True
            result["field_type"] = "standard"
            result["access_pattern"] = f"args.Current.{field_name}"
            
        elif field_name in metadata["custom_fields"]:
            result["exists"] = True  
            result["field_type"] = "custom"
            # Custom fields may need bracket notation if they have spaces
            if ' ' in field_name or '-' in field_name:
                result["access_pattern"] = f'args.Current["{field_name}"]'
            else:
                result["access_pattern"] = f"args.Current.{field_name}"
        
        return result
    
    def test_connection(self) -> bool:
        """Test if the API connection works"""
        try:
            result = self._make_request("Context")
            return result is not None and 'LoggedUser' in result
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False