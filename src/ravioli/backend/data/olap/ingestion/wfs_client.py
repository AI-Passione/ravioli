import httpx
import xml.etree.ElementTree as ET
import pandas as pd
import io
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class WFSClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.timeout = 30.0

    async def get_capabilities(self) -> List[Dict[str, Any]]:
        logger.info(f"Fetching WFS Capabilities from {self.base_url}")
        params = {
            "service": "WFS",
            "version": "2.0.0",
            "request": "GetCapabilities"
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(self.base_url, params=params)
            response.raise_for_status()
        
        logger.debug("Parsing GetCapabilities response XML")
        root = ET.fromstring(response.text)
        
        # Namespaces for WFS 2.0.0
        ns = {
            'wfs': 'http://www.opengis.net/wfs/2.0',
            'ows': 'http://www.opengis.net/ows/1.1'
        }
        
        layers = []
        feature_type_list = root.find('.//wfs:FeatureTypeList', ns)
        if feature_type_list is not None:
            for feature_type in feature_type_list.findall('wfs:FeatureType', ns):
                name_el = feature_type.find('wfs:Name', ns)
                title_el = feature_type.find('wfs:Title', ns)
                
                name = name_el.text if name_el is not None else "Unknown"
                title = title_el.text if title_el is not None else name
                
                # Check output formats
                formats_el = feature_type.find('wfs:OutputFormats', ns)
                formats = []
                if formats_el is not None:
                    formats = [f.text for f in formats_el.findall('wfs:Format', ns)]
                
                layers.append({
                    "name": name,
                    "title": title,
                    "formats": formats
                })
        
        return layers

    async def get_features_generator(self, layer_name: str, chunk_size: int = 1000, output_format: Optional[str] = None):
        logger.info(f"Requesting features for layer {layer_name} with pagination (chunk_size={chunk_size}, format={output_format})")
        
        start_index = 0
        while True:
            params = {
                "service": "WFS",
                "version": "2.0.0",
                "request": "GetFeature",
                "typeNames": layer_name,
                "count": str(chunk_size),
                "startIndex": str(start_index)
            }
            
            if output_format:
                params["outputFormat"] = output_format
            else:
                params["outputFormat"] = "application/json"

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.debug(f"Sending GetFeature request to {self.base_url} at startIndex {start_index}")
                response = await client.get(self.base_url, params=params)
                if response.status_code != 200 and not output_format:
                    logger.warning(f"JSON request failed (HTTP {response.status_code}), falling back to CSV")
                    params["outputFormat"] = "csv"
                    response = await client.get(self.base_url, params=params)
                response.raise_for_status()

            content_type = response.headers.get("Content-Type", "")
            logger.info(f"Received response with content-type: {content_type}")
            
            features_yielded = 0
            if "application/json" in content_type or "json" in response.text[:100].lower():
                data = response.json()
                features = data.get("features", [])
                for feat in features:
                    yield feat.get("properties", {})
                    features_yielded += 1
                
            elif "csv" in content_type or "," in response.text[:100]:
                df = pd.read_csv(io.StringIO(response.text))
                for _, row in df.iterrows():
                    yield row.to_dict()
                    features_yielded += 1
            else:
                raise ValueError(f"Unsupported response format: {content_type}")

            if features_yielded < chunk_size:
                # We reached the end of the dataset
                break
                
            start_index += chunk_size

    async def get_features(self, layer_name: str, chunk_size: int = 1000, output_format: Optional[str] = None) -> pd.DataFrame:
        rows = []
        async for row in self.get_features_generator(layer_name, chunk_size, output_format):
            rows.append(row)
        return pd.DataFrame(rows)
