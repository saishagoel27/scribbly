import logging
import time
import base64
from typing import Dict, List, Optional, Tuple, Callable
import json
from datetime import datetime
import io

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import AzureError, ResourceNotFoundError, HttpResponseError, ServiceRequestError

from config import Config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AzureDocumentProcessor:
    """
    Azure Document Intelligence processor with comprehensive OCR capabilities
    Following Azure best practices for Document Intelligence API
    """
    
    def __init__(self):
        """Initialize Azure Document Intelligence client"""
        self.client = None
        self.is_available = False
        self.endpoint = Config.AZURE_DOC_INTELLIGENCE_ENDPOINT
        self.key = Config.AZURE_DOC_INTELLIGENCE_KEY
        self.timeout = Config.AZURE_TIMEOUT
        self.max_retries = 3
        
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize Azure Document Intelligence client with error handling"""
        try:
            if not self.endpoint or not self.key:
                logger.warning("❌ Azure Document Intelligence credentials not configured")
                self.is_available = False
                return
            
            # Validate endpoint format
            if not self.endpoint.startswith('https://'):
                logger.error("❌ Invalid Azure endpoint format. Must start with https://")
                self.is_available = False
                return
            
            # Create client with proper credentials and API version
            credential = AzureKeyCredential(self.key)
            self.client = DocumentIntelligenceClient(
                endpoint=self.endpoint,
                credential=credential,
                api_version="2024-02-29-preview"  # Use the same API version as your working code
            )
            
            # Test connection
            self._test_connection()
            self.is_available = True
            logger.info("✅ Azure Document Intelligence client initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Azure Document Intelligence: {e}")
            self.is_available = False
    
    def _test_connection(self) -> None:
        """Test Azure connection with minimal validation"""
        try:
            # Simple validation - check if client is properly configured
            if self.client and self.endpoint and self.key:
                logger.info("🔗 Azure Document Intelligence connection configured")
            else:
                raise Exception("Client configuration incomplete")
        except Exception as e:
            logger.warning(f"⚠️ Azure connection test failed: {e}")
            raise
    
    def extract_text_with_handwriting(self, 
                                    file_bytes: bytes, 
                                    content_type: str, 
                                    progress_callback: Optional[Callable[[str], None]] = None) -> Dict:
        """
        Extract text from documents with handwriting recognition using Azure Document Intelligence
        Using the same method structure that was working in your previous code
        """
        if not self.is_available:
            return self._create_fallback_response("Azure Document Intelligence not available")
        
        try:
            if progress_callback:
                progress_callback("🔍 Starting Azure OCR analysis...")
            
            # METHOD 1: AnalyzeDocumentRequest with base64_source (your working method)
            try:
                if progress_callback:
                    progress_callback("📝 Processing with AnalyzeDocumentRequest method...")
                
                # Create base64 encoded content
                base64_source = base64.b64encode(file_bytes).decode('utf-8')
                
                # Create the request body using the working pattern
                analyze_request = AnalyzeDocumentRequest(
                    base64_source=base64_source
                )
                
                poller = self.client.begin_analyze_document(
                    model_id="prebuilt-read",
                    analyze_request=analyze_request
                )
                
                if progress_callback:
                    progress_callback("⏳ Azure processing document...")
                
                result = poller.result()
                extracted_data = self._process_analysis_result_optimized(result)
                
                if extracted_data.get("content") and len(extracted_data["content"].strip()) > 0:
                    logger.info(f"✅ Method 1 SUCCESS: {len(extracted_data['content'])} characters")
                    return self._format_success_response(extracted_data)
                else:
                    raise Exception("No content extracted from method 1")
                    
            except Exception as method1_error:
                logger.warning(f"Method 1 failed: {method1_error}")
                
                # METHOD 2: Try with BytesIO stream (your working fallback)
                try:
                    if progress_callback:
                        progress_callback("🔄 Trying alternative BytesIO method...")
                    
                    # Reset for second attempt using BytesIO
                    document_stream = io.BytesIO(file_bytes)
                    document_stream.seek(0)
                    
                    poller = self.client.begin_analyze_document(
                        model_id="prebuilt-read",
                        analyze_request=document_stream,
                        content_type=content_type or "application/octet-stream"
                    )
                    
                    result = poller.result()
                    extracted_data = self._process_analysis_result_optimized(result)
                    
                    if extracted_data.get("content") and len(extracted_data["content"].strip()) > 0:
                        logger.info(f"✅ Method 2 SUCCESS: {len(extracted_data['content'])} characters")
                        return self._format_success_response(extracted_data)
                    else:
                        raise Exception("No content extracted from method 2")
                        
                except Exception as method2_error:
                    logger.warning(f"Method 2 failed: {method2_error}")
                    
                    # METHOD 3: Legacy compatibility pattern (your working final fallback)
                    try:
                        if progress_callback:
                            progress_callback("🔄 Trying legacy compatibility method...")
                        
                        # Try the older parameter structure exactly as in your working code
                        poller = self.client.begin_analyze_document(
                            "prebuilt-read",
                            file_bytes,
                            content_type=content_type or "application/octet-stream"
                        )
                        
                        result = poller.result()
                        extracted_data = self._process_analysis_result_optimized(result)
                        
                        logger.info(f"✅ Method 3 SUCCESS: {len(extracted_data['content'])} characters")
                        return self._format_success_response(extracted_data)
                        
                    except Exception as method3_error:
                        logger.error(f"All methods failed. Last error: {method3_error}")
                        error_msg = f"Document analysis failed after trying all methods: {str(method3_error)}"
                        return self._create_error_response(error_msg)
            
        except Exception as e:
            error_msg = f"Azure OCR failed: {str(e)}"
            logger.error(error_msg)
            return self._create_error_response(error_msg)
    
    def comprehensive_document_analysis(self, 
                                      file_bytes: bytes, 
                                      content_type: str, 
                                      file_info: Dict,
                                      progress_callback: Optional[Callable[[str], None]] = None) -> Dict:
        """
        Perform comprehensive document analysis including layout, tables, and text
        """
        if not self.is_available:
            return self._create_fallback_response("Azure Document Intelligence not available")
        
        results = {
            "text_extraction": {},
            "layout_analysis": {},
            "table_extraction": {},
            "handwriting_analysis": {},
            "quality_metrics": {},
            "metadata": {},
            "summary_optimization": {}
        }
        
        try:
            if progress_callback:
                progress_callback("🧠 Running comprehensive analysis...")
            
            # 1. Text Extraction using the working method
            text_result = self.extract_text_with_handwriting(
                file_bytes, content_type, progress_callback
            )
            
            if text_result.get("status") == "success":
                results["text_extraction"] = text_result.get("text_extraction", {})
                
                # 2. Layout Analysis (if text extraction succeeded)
                extracted_content = results["text_extraction"].get("extracted_text", "")
                
                if extracted_content and len(extracted_content.strip()) > 10:
                    if progress_callback:
                        progress_callback("📋 Analyzing document structure...")
                    
                    try:
                        # Try layout analysis with the same working pattern
                        base64_source = base64.b64encode(file_bytes).decode('utf-8')
                        layout_request = AnalyzeDocumentRequest(base64_source=base64_source)
                        
                        layout_poller = self.client.begin_analyze_document(
                            model_id="prebuilt-layout",
                            analyze_request=layout_request
                        )
                        
                        layout_result = layout_poller.result()
                        results["layout_analysis"] = self._process_layout_result_optimized(layout_result)
                        results["table_extraction"] = self._extract_tables_optimized(layout_result)
                        
                        results["summary_optimization"] = self._optimize_for_summary(
                            results["text_extraction"], 
                            results["layout_analysis"]
                        )
                        
                    except Exception as layout_error:
                        logger.warning(f"Layout analysis failed: {layout_error}")
                        results["layout_analysis"] = {"status": "failed", "error": str(layout_error)}
                        results["table_extraction"] = {"tables": [], "status": "failed"}
                        results["summary_optimization"] = {"status": "basic", "note": "Using text-only optimization"}
                
                # 3. Generate quality metrics
                results["handwriting_analysis"] = self._analyze_handwriting_quality_enhanced(results["text_extraction"])
                results["quality_metrics"] = self._generate_quality_metrics_enhanced(results)
                results["metadata"] = self._compile_metadata_enhanced(results, file_info)
            
            else:
                # Text extraction failed
                return text_result
            
            if progress_callback:
                progress_callback("✅ Comprehensive analysis complete!")
            
            return {
                "status": "success",
                "comprehensive_analysis": results,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Comprehensive analysis failed: {str(e)}"
            logger.error(error_msg)
            return self._create_error_response(error_msg)
    
    def _process_analysis_result_optimized(self, result):
        """
        Process analysis result using the same structure as your working code
        """
        extracted_data = {
            "content": "",
            "structured_content": {},
            "pages": [],
            "paragraphs": [],
            "lines": [],
            "words": [],
            "handwriting_confidence": [],
            "content_hierarchy": [],
            "metadata": {}
        }
        
        try:
            # Extract raw content - this is the main text
            raw_content = getattr(result, 'content', '') or ""
            extracted_data["content"] = raw_content
            
            content_sections = []
            
            # Process pages if available
            if hasattr(result, 'pages') and result.pages:
                for page_num, page in enumerate(result.pages, 1):
                    page_data = {
                        "page_number": page_num,
                        "width": getattr(page, 'width', 0),
                        "height": getattr(page, 'height', 0),
                        "angle": getattr(page, 'angle', 0),
                        "lines": [],
                        "words": [],
                        "quality_score": 0.0
                    }
                    
                    page_confidences = []
                    
                    # Process lines
                    if hasattr(page, 'lines') and page.lines:
                        for line_idx, line in enumerate(page.lines):
                            line_content = getattr(line, 'content', '')
                            line_confidence = getattr(line, 'confidence', 0.0)
                            
                            line_data = {
                                "content": line_content,
                                "confidence": line_confidence,
                                "line_index": line_idx,
                                "importance_score": self._calculate_line_importance(line_content)
                            }
                            
                            page_data["lines"].append(line_data)
                            extracted_data["lines"].append(line_data)
                            
                            if line_confidence > 0:
                                extracted_data["handwriting_confidence"].append(line_confidence)
                                page_confidences.append(line_confidence)
                            
                            # Add to content hierarchy if important
                            if line_data["importance_score"] > 0.7:
                                content_sections.append({
                                    "content": line_content,
                                    "confidence": line_confidence,
                                    "importance": line_data["importance_score"],
                                    "page": page_num
                                })
                    
                    # Calculate page quality score
                    if page_confidences:
                        page_data["quality_score"] = sum(page_confidences) / len(page_confidences)
                    
                    # Process words
                    if hasattr(page, 'words') and page.words:
                        for word in page.words:
                            word_data = {
                                "content": getattr(word, 'content', ''),
                                "confidence": getattr(word, 'confidence', 0.0),
                                "page": page_num
                            }
                            page_data["words"].append(word_data)
                            extracted_data["words"].append(word_data)
                    
                    extracted_data["pages"].append(page_data)
            
            # Process paragraphs if available
            if hasattr(result, 'paragraphs') and result.paragraphs:
                for para_idx, paragraph in enumerate(result.paragraphs):
                    para_content = getattr(paragraph, 'content', '')
                    para_role = getattr(paragraph, 'role', 'paragraph')
                    
                    para_data = {
                        "content": para_content,
                        "role": para_role,
                        "confidence": getattr(paragraph, 'confidence', 0.0),
                        "hierarchy_level": self._determine_hierarchy_level(para_role, para_content),
                        "summary_relevance": self._calculate_summary_relevance(para_content)
                    }
                    extracted_data["paragraphs"].append(para_data)
            
            # Create content hierarchy
            extracted_data["content_hierarchy"] = sorted(
                content_sections, 
                key=lambda x: (x["importance"], x["confidence"]), 
                reverse=True
            )
            
            # Create structured content
            extracted_data["structured_content"] = {
                "high_priority": [item["content"] for item in extracted_data["content_hierarchy"][:5]],
                "medium_priority": [item["content"] for item in extracted_data["content_hierarchy"][5:15]],
                "full_content": raw_content,
                "total_sections": len(content_sections)
            }
            
            # Calculate metadata
            avg_confidence = (
                sum(extracted_data["handwriting_confidence"]) / len(extracted_data["handwriting_confidence"]) 
                if extracted_data["handwriting_confidence"] else 0.0
            )
            
            extracted_data["metadata"] = {
                "model_id": getattr(result, 'model_id', 'prebuilt-read'),
                "api_version": getattr(result, 'api_version', '2024-02-29-preview'),
                "page_count": len(extracted_data["pages"]),
                "total_lines": len(extracted_data["lines"]),
                "total_words": len(extracted_data["words"]),
                "character_count": len(raw_content),
                "average_confidence": avg_confidence,
                "quality_score": min(avg_confidence * 1.2, 1.0),
                "has_handwriting": len(extracted_data["handwriting_confidence"]) > 0,
                "summary_readiness": self._assess_summary_readiness(extracted_data),
                "processing_successful": True,
                "optimization_level": "enhanced"
            }
            
        except Exception as processing_error:
            logger.error(f"Error in processing: {processing_error}")
            extracted_data["metadata"] = {
                "processing_successful": False,
                "error": str(processing_error),
                "optimization_level": "failed"
            }
        
        return extracted_data
    
    def _calculate_line_importance(self, line_content: str) -> float:
        """Calculate importance score for a line of text"""
        if not line_content or len(line_content.strip()) < 3:
            return 0.0
        
        importance_indicators = [
            (lambda x: x.isupper() and len(x) < 100, 0.9),
            (lambda x: any(word in x.lower() for word in ['title', 'heading', 'subject']), 0.8),
            (lambda x: any(char in x for char in [':', '•', '-', '1.', '2.']), 0.7),
            (lambda x: any(word in x.lower() for word in ['important', 'note', 'summary', 'conclusion']), 0.8),
            (lambda x: any(char.isdigit() for char in x), 0.6),
            (lambda x: 20 <= len(x) <= 200, 0.5),
        ]
        
        max_score = 0.0
        for condition, score in importance_indicators:
            try:
                if condition(line_content):
                    max_score = max(max_score, score)
            except:
                continue
        
        return max_score
    
    def _determine_hierarchy_level(self, role: str, content: str) -> int:
        """Determine hierarchy level of content"""
        hierarchy_map = {
            'title': 1, 'sectionHeading': 2, 'heading': 3, 'subheading': 4, 'paragraph': 5
        }
        
        level = hierarchy_map.get(role, 5)
        
        if content and len(content) < 50 and content.isupper():
            level = min(level, 2)
        
        return level
    
    def _calculate_summary_relevance(self, content: str) -> float:
        """Calculate how relevant content is for summarization"""
        if not content:
            return 0.0
        
        relevance_score = 0.5
        
        key_phrases = ['summary', 'conclusion', 'result', 'finding', 'important', 'key', 'main']
        for phrase in key_phrases:
            if phrase in content.lower():
                relevance_score += 0.1
        
        if 50 <= len(content) <= 300:
            relevance_score += 0.2
        
        if len(content) < 10 or len(content) > 500:
            relevance_score -= 0.2
        
        return min(relevance_score, 1.0)
    
    def _assess_summary_readiness(self, extracted_data: dict) -> str:
        """Assess how ready the content is for summarization"""
        content_length = len(extracted_data.get("content", ""))
        avg_confidence = extracted_data.get("metadata", {}).get("average_confidence", 0.0)
        hierarchy_items = len(extracted_data.get("content_hierarchy", []))
        
        if content_length > 500 and avg_confidence > 0.8 and hierarchy_items > 3:
            return "excellent"
        elif content_length > 200 and avg_confidence > 0.6:
            return "good"
        elif content_length > 50:
            return "fair"
        else:
            return "poor"
    
    def _process_layout_result_optimized(self, result):
        """Process layout analysis results"""
        layout_data = {
            "sections": [],
            "document_structure": {},
            "summary_sections": [],
            "processing_successful": True
        }
        
        try:
            if hasattr(result, 'paragraphs') and result.paragraphs:
                for paragraph in result.paragraphs:
                    content = getattr(paragraph, 'content', '')
                    role = getattr(paragraph, 'role', 'paragraph')
                    
                    section_data = {
                        "content": content,
                        "role": role,
                        "confidence": getattr(paragraph, 'confidence', 0.0),
                        "summary_priority": self._calculate_summary_relevance(content)
                    }
                    layout_data["sections"].append(section_data)
                    
                    if section_data["summary_priority"] > 0.7:
                        layout_data["summary_sections"].append(section_data)
            
            layout_data["document_structure"] = {
                "total_sections": len(layout_data["sections"]),
                "summary_ready_sections": len(layout_data["summary_sections"]),
                "has_structure": len(layout_data["sections"]) > 0,
                "structure_quality": "good" if len(layout_data["summary_sections"]) > 2 else "basic"
            }
            
        except Exception as e:
            logger.error(f"Error processing layout: {e}")
            layout_data["processing_successful"] = False
            layout_data["error"] = str(e)
        
        return layout_data
    
    def _extract_tables_optimized(self, result):
        """Extract and optimize table data"""
        table_data = {
            "tables": [],
            "summary_relevant_tables": [],
            "processing_successful": True
        }
        
        try:
            if hasattr(result, 'tables') and result.tables:
                for i, table in enumerate(result.tables):
                    table_info = {
                        "table_id": i,
                        "row_count": getattr(table, 'row_count', 0),
                        "column_count": getattr(table, 'column_count', 0),
                        "cells": [],
                        "summary_relevance": 0.0
                    }
                    
                    table_content = []
                    if hasattr(table, 'cells') and table.cells:
                        for cell in table.cells:
                            cell_content = getattr(cell, 'content', '')
                            cell_data = {
                                "content": cell_content,
                                "row_index": getattr(cell, 'row_index', 0),
                                "column_index": getattr(cell, 'column_index', 0)
                            }
                            table_info["cells"].append(cell_data)
                            table_content.append(cell_content)
                    
                    full_table_text = " ".join(table_content)
                    table_info["summary_relevance"] = self._calculate_summary_relevance(full_table_text)
                    
                    table_data["tables"].append(table_info)
                    
                    if table_info["summary_relevance"] > 0.6:
                        table_data["summary_relevant_tables"].append(table_info)
        
        except Exception as e:
            logger.error(f"Error extracting tables: {e}")
            table_data["processing_successful"] = False
            table_data["error"] = str(e)
        
        return table_data
    
    def _optimize_for_summary(self, text_extraction: dict, layout_analysis: dict) -> dict:
        """Optimize content for summary generation"""
        optimization = {
            "summary_ready_content": [],
            "key_sections": [],
            "optimization_score": 0.0,
            "recommendations": []
        }
        
        try:
            content_hierarchy = text_extraction.get("content_hierarchy", [])
            
            for item in content_hierarchy[:10]:
                if len(item["content"]) > 20:
                    optimization["summary_ready_content"].append({
                        "text": item["content"],
                        "confidence": item["confidence"],
                        "importance": item["importance"],
                        "page": item["page"]
                    })
            
            layout_sections = layout_analysis.get("summary_sections", [])
            for section in layout_sections:
                optimization["key_sections"].append({
                    "text": section["content"],
                    "role": section["role"],
                    "priority": section["summary_priority"]
                })
            
            content_quality = text_extraction.get("metadata", {}).get("quality_score", 0.0)
            structure_quality = 1.0 if layout_analysis.get("document_structure", {}).get("structure_quality") == "good" else 0.5
            content_amount = min(len(optimization["summary_ready_content"]) / 10.0, 1.0)
            
            optimization["optimization_score"] = (content_quality + structure_quality + content_amount) / 3.0
            
            if optimization["optimization_score"] < 0.6:
                optimization["recommendations"].append("Document quality may affect summary accuracy")
            if len(optimization["summary_ready_content"]) < 3:
                optimization["recommendations"].append("Limited structured content detected")
            if optimization["optimization_score"] >= 0.8:
                optimization["recommendations"].append("Excellent content for high-quality summaries")
            
        except Exception as e:
            logger.error(f"Error optimizing for summary: {e}")
            optimization["error"] = str(e)
        
        return optimization
    
    def _analyze_handwriting_quality_enhanced(self, text_extraction_result: dict) -> Dict:
        """Analyze handwriting recognition quality"""
        analysis = {
            "handwriting_detected": False,
            "confidence_distribution": {},
            "quality_score": 0.0,
            "summary_impact": "none",
            "recommendations": []
        }
        
        try:
            confidences = text_extraction_result.get("handwriting_confidence", [])
            
            if confidences and len(confidences) > 0:
                analysis["handwriting_detected"] = True
                
                high_conf = sum(1 for c in confidences if c >= 0.8)
                med_conf = sum(1 for c in confidences if 0.5 <= c < 0.8)
                low_conf = sum(1 for c in confidences if c < 0.5)
                
                total = len(confidences)
                analysis["confidence_distribution"] = {
                    "high_confidence": round((high_conf / total) * 100, 1),
                    "medium_confidence": round((med_conf / total) * 100, 1),
                    "low_confidence": round((low_conf / total) * 100, 1)
                }
                
                avg_confidence = sum(confidences) / len(confidences)
                analysis["quality_score"] = round(avg_confidence, 3)
                
                if avg_confidence >= 0.8:
                    analysis["summary_impact"] = "minimal"
                    analysis["recommendations"].append("Excellent handwriting recognition")
                elif avg_confidence >= 0.6:
                    analysis["summary_impact"] = "low"
                    analysis["recommendations"].append("Good handwriting recognition")
                else:
                    analysis["summary_impact"] = "moderate"
                    analysis["recommendations"].append("Handwriting recognition quality may affect results")
        
        except Exception as e:
            logger.error(f"Error in handwriting analysis: {e}")
        
        return analysis
    
    def _generate_quality_metrics_enhanced(self, results: dict) -> Dict:
        """Generate comprehensive quality metrics"""
        metrics = {
            "overall_quality": "Unknown",
            "text_extraction_quality": 0.0,
            "summary_readiness": "Unknown",
            "optimization_score": 0.0,
            "recommendations": []
        }
        
        try:
            text_quality = results.get("text_extraction", {}).get("metadata", {}).get("quality_score", 0.0)
            summary_readiness = results.get("text_extraction", {}).get("metadata", {}).get("summary_readiness", "unknown")
            optimization_score = results.get("summary_optimization", {}).get("optimization_score", 0.0)
            
            metrics["text_extraction_quality"] = text_quality
            metrics["summary_readiness"] = summary_readiness
            metrics["optimization_score"] = optimization_score
            
            overall_score = (text_quality + optimization_score) / 2.0
            
            if overall_score >= 0.9:
                metrics["overall_quality"] = "Excellent"
                metrics["recommendations"].append("Perfect for high-quality summaries")
            elif overall_score >= 0.7:
                metrics["overall_quality"] = "Good"
                metrics["recommendations"].append("Good quality for reliable summaries")
            elif overall_score >= 0.5:
                metrics["overall_quality"] = "Fair"
                metrics["recommendations"].append("Adequate for basic summaries")
            else:
                metrics["overall_quality"] = "Poor"
                metrics["recommendations"].append("Summary quality may be limited")
        
        except Exception as e:
            logger.error(f"Error generating metrics: {e}")
        
        return metrics
    
    def _compile_metadata_enhanced(self, results: dict, file_info: dict) -> Dict:
        """Compile comprehensive metadata"""
        try:
            text_stats = results.get("text_extraction", {}).get("metadata", {})
            summary_opt = results.get("summary_optimization", {})
            
            return {
                "file_info": file_info,
                "processing_timestamp": datetime.now().isoformat(),
                "api_version": "2024-02-29-preview",
                "optimization_level": "enhanced",
                "models_used": ["prebuilt-read", "prebuilt-layout"],
                "content_statistics": {
                    "character_count": text_stats.get("character_count", 0),
                    "word_count": len(results.get("text_extraction", {}).get("content", "").split()),
                    "page_count": text_stats.get("page_count", 0),
                    "line_count": text_stats.get("total_lines", 0),
                    "summary_ready_sections": len(summary_opt.get("summary_ready_content", []))
                },
                "quality_indicators": {
                    "extraction_quality": text_stats.get("quality_score", 0.0),
                    "summary_readiness": text_stats.get("summary_readiness", "unknown"),
                    "optimization_score": summary_opt.get("optimization_score", 0.0),
                    "has_structure": len(summary_opt.get("key_sections", [])) > 0
                },
                "summary_optimization": {
                    "content_hierarchy_items": len(results.get("text_extraction", {}).get("content_hierarchy", [])),
                    "structured_sections": len(summary_opt.get("key_sections", [])),
                    "ready_for_ai_summary": summary_opt.get("optimization_score", 0.0) > 0.6
                }
            }
        except Exception as e:
            logger.error(f"Error compiling metadata: {e}")
            return {"error": str(e)}
    
    def _format_success_response(self, extracted_data: dict) -> Dict:
        """Format successful extraction response"""
        return {
            "status": "success",
            "text_extraction": {
                "extracted_text": extracted_data.get("content", ""),
                "text_blocks": extracted_data.get("lines", []),
                "handwriting_detected": len(extracted_data.get("handwriting_confidence", [])) > 0,
                "confidence_scores": extracted_data.get("handwriting_confidence", []),
                "total_pages": extracted_data.get("metadata", {}).get("page_count", 0),
                "processing_metadata": extracted_data.get("metadata", {}),
                "optimized_text": extracted_data.get("content", "")
            },
            "timestamp": datetime.now().isoformat(),
            "azure_model_used": "prebuilt-read"
        }
    
    def _create_fallback_response(self, message: str) -> Dict:
        """Create fallback response when Azure is not available"""
        return {
            "status": "fallback",
            "message": message,
            "text_extraction": {
                "extracted_text": "",
                "processing_metadata": {
                    "azure_available": False,
                    "fallback_used": True
                }
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def _create_error_response(self, error_message: str) -> Dict:
        """Create standardized error response"""
        return {
            "status": "error",
            "error": error_message,
            "text_extraction": {
                "extracted_text": "",
                "processing_metadata": {
                    "error_occurred": True,
                    "azure_available": self.is_available
                }
            },
            "timestamp": datetime.now().isoformat()
        }

# Create global instance
azure_document_processor = AzureDocumentProcessor()