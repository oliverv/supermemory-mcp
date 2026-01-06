#!/usr/bin/env python3
"""
Supermemory MCP Server
A Model Context Protocol server for managing memories and knowledge.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SupermemoryServer:
    def __init__(self):
        self.memories: List[Dict[str, Any]] = []
        self.server = Server("supermemory")
        self._setup_tools()

    def _setup_tools(self):
        """Setup MCP tools"""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            return [
                Tool(
                    name="add_memory",
                    description="Store a new memory or piece of information",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "content": {"type": "string", "description": "The content to remember"},
                            "title": {"type": "string", "description": "Title for the memory"},
                            "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags for categorization"}
                        },
                        "required": ["content", "title"]
                    }
                ),
                Tool(
                    name="search_memories",
                    description="Search through stored memories",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "limit": {"type": "integer", "description": "Maximum number of results", "default": 10}
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="list_memories",
                    description="List all stored memories",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "limit": {"type": "integer", "description": "Maximum number of memories to return", "default": 20}
                        }
                    }
                ),
                Tool(
                    name="delete_memory",
                    description="Delete a specific memory by ID",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "memory_id": {"type": "integer", "description": "ID of the memory to delete"}
                        },
                        "required": ["memory_id"]
                    }
                ),
                Tool(
                    name="get_memory",
                    description="Get a specific memory by ID",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "memory_id": {"type": "integer", "description": "ID of the memory to retrieve"}
                        },
                        "required": ["memory_id"]
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            try:
                if name == "add_memory":
                    return await self._add_memory(arguments)
                elif name == "search_memories":
                    return await self._search_memories(arguments)
                elif name == "list_memories":
                    return await self._list_memories(arguments)
                elif name == "delete_memory":
                    return await self._delete_memory(arguments)
                elif name == "get_memory":
                    return await self._get_memory(arguments)
                else:
                    return [TextContent(type="text", text=f"Unknown tool: {name}")]
            except Exception as e:
                logger.error(f"Error in tool {name}: {e}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]

    async def _add_memory(self, args: Dict[str, Any]) -> List[TextContent]:
        """Add a new memory"""
        memory_id = len(self.memories) + 1
        memory = {
            "id": memory_id,
            "title": args["title"],
            "content": args["content"],
            "tags": args.get("tags", []),
            "created_at": asyncio.get_event_loop().time()
        }
        self.memories.append(memory)
        
        return [TextContent(
            type="text",
            text=f"Memory added successfully with ID: {memory_id}\nTitle: {memory['title']}"
        )]

    async def _search_memories(self, args: Dict[str, Any]) -> List[TextContent]:
        """Search memories by query"""
        query = args["query"].lower()
        limit = args.get("limit", 10)
        
        results = []
        for memory in self.memories:
            if (query in memory["title"].lower() or 
                query in memory["content"].lower() or 
                any(query in tag.lower() for tag in memory["tags"])):
                results.append(memory)
        
        results = results[:limit]
        
        if not results:
            return [TextContent(type="text", text=f"No memories found for query: {query}")]
        
        result_text = f"Found {len(results)} memories:\n\n"
        for memory in results:
            result_text += f"ID: {memory['id']}\nTitle: {memory['title']}\nContent: {memory['content'][:100]}...\nTags: {', '.join(memory['tags'])}\n\n"
        
        return [TextContent(type="text", text=result_text)]

    async def _list_memories(self, args: Dict[str, Any]) -> List[TextContent]:
        """List all memories"""
        limit = args.get("limit", 20)
        memories = self.memories[:limit]
        
        if not memories:
            return [TextContent(type="text", text="No memories stored yet.")]
        
        result_text = f"Total memories: {len(self.memories)}\nShowing first {len(memories)}:\n\n"
        for memory in memories:
            result_text += f"ID: {memory['id']}\nTitle: {memory['title']}\nTags: {', '.join(memory['tags'])}\n\n"
        
        return [TextContent(type="text", text=result_text)]

    async def _delete_memory(self, args: Dict[str, Any]) -> List[TextContent]:
        """Delete a memory by ID"""
        memory_id = args["memory_id"]
        
        for i, memory in enumerate(self.memories):
            if memory["id"] == memory_id:
                deleted_memory = self.memories.pop(i)
                return [TextContent(
                    type="text",
                    text=f"Memory deleted successfully:\nID: {deleted_memory['id']}\nTitle: {deleted_memory['title']}"
                )]
        
        return [TextContent(type="text", text=f"Memory with ID {memory_id} not found.")]

    async def _get_memory(self, args: Dict[str, Any]) -> List[TextContent]:
        """Get a specific memory by ID"""
        memory_id = args["memory_id"]
        
        for memory in self.memories:
            if memory["id"] == memory_id:
                result_text = f"ID: {memory['id']}\nTitle: {memory['title']}\nContent: {memory['content']}\nTags: {', '.join(memory['tags'])}"
                return [TextContent(type="text", text=result_text)]
        
        return [TextContent(type="text", text=f"Memory with ID {memory_id} not found.")]

async def main():
    """Main entry point"""
    server_instance = SupermemoryServer()
    
    async with stdio_server() as (read_stream, write_stream):
        await server_instance.server.run(
            read_stream,
            write_stream,
            server_instance.server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
