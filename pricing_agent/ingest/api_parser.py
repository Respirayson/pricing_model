import re
from typing import List, Optional, Dict, Any
from ..api_schemas import APIDefinition, APIParameter, APIField


class APIDefinitionParser:
    
    def parse_file(self, file_path: str) -> List[APIDefinition]:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return self.parse_content(content)
    
    def parse_content(self, content: str) -> List[APIDefinition]:
        api_definitions = []
        section_pattern = r'#\s*={40,}\s*\n\s*#\s*\d+\)\s*(.+?)\s*\n\s*#\s*={40,}\s*\n(.*?)(?=#\s*={40,}|$)'
        
        for match in re.finditer(section_pattern, content, re.DOTALL):
            api_name = match.group(1).strip()
            section_content = match.group(2).strip()
            
            if not section_content:
                continue
            
            code_blocks = re.findall(r'```python\s*\n(.*?)```', section_content, re.DOTALL)
            
            if len(code_blocks) >= 1:
                all_params = []
                all_fields = []
                
                for code_block in code_blocks:
                    dataclass_pattern = r'@dataclass\s+class\s+\w+.*?(?=@dataclass|$)'
                    dataclasses = re.findall(dataclass_pattern, code_block, re.DOTALL)
                    
                    for dc in dataclasses:
                        if 'Input' in dc:
                            all_params.extend(self._parse_dataclass(dc, is_input=True))
                        elif 'Output' in dc:
                            all_fields.extend(self._parse_dataclass(dc, is_input=False))
                
                if all_params or all_fields:
                    api_id = self._generate_api_id(api_name)
                    category = self._infer_category(api_name, all_params, all_fields)
                    
                    api_def = APIDefinition(
                        api_id=api_id,
                        name=api_name,
                        description=api_name,
                        input_params=all_params,
                        output_fields=all_fields,
                        category=category,
                        region="ANY",
                        raw_definition=match.group(0).strip()
                    )
                    
                    api_definitions.append(api_def)
        
        return api_definitions
    
    def _parse_dataclass(self, code: str, is_input: bool = None) -> List:
        fields = []
        
        if is_input is None:
            dataclass_match = re.search(r'class\s+(\w+)', code)
            is_input = 'Input' in dataclass_match.group(1) if dataclass_match else False
        
        field_pattern = r'(\w+):\s*([^\n=]+?)(?:\s*=\s*([^\n#]+?))?(?:\s*#\s*(.+?))?$'
        for match in re.finditer(field_pattern, code, re.MULTILINE):
            field_name = match.group(1).strip()
            field_type = match.group(2).strip()
            default_value = match.group(3).strip() if match.group(3) else None
            comment = match.group(4).strip() if match.group(4) else None
            
            if field_name in ['dataclass', 'class']:
                continue
            
            required = default_value is None and 'Optional' not in field_type
            is_array = 'List[' in field_type or 'list[' in field_type.lower()
            clean_type = self._clean_type(field_type)
            
            if is_input:
                fields.append(APIParameter(
                    name=field_name,
                    type=clean_type,
                    required=required,
                    description=comment
                ))
            else:
                fields.append(APIField(
                    name=field_name,
                    type=clean_type,
                    is_array=is_array,
                    description=comment
                ))
        
        return fields
    
    def _clean_type(self, type_str: str) -> str:
        type_str = re.sub(r'Optional\[(.*?)\]', r'\1', type_str)
        type_str = re.sub(r'List\[(.*?)\]', r'List[\1]', type_str)
        return type_str.strip()
    
    def _generate_api_id(self, api_name: str) -> str:
        api_id = api_name.lower()
        api_id = re.sub(r'[^\w\s-]', '', api_id)
        api_id = re.sub(r'[\s-]+', '_', api_id)
        return api_id
    
    def _infer_category(self, api_name: str, input_params: List, output_fields: List) -> str:
        name_lower = api_name.lower()
        categories = [
            (['customer', 'search', 'list'], 'customer'),
            (['document', 'verify', 'id', 'passport'], 'document'),
            (['contact', 'participant'], 'contact'),
            (['device', 'group'], 'device'),
            (['priority', 'star'], 'premium'),
            (['real', 'name', 'authentication', 'check'], 'verification'),
            (['onboarding', 'photo'], 'onboarding')
        ]
        for keywords, category in categories:
            if any(kw in name_lower for kw in keywords):
                return category
        return 'general'


def load_apis_from_file(file_path: str) -> List[APIDefinition]:
    parser = APIDefinitionParser()
    return parser.parse_file(file_path)

