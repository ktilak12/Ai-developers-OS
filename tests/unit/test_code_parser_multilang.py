"""
Tests for multi-language AST parsing (Python, TS, Go, Rust, Java, C/C++) in CodeParser.
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from intelligence.parser.code_parser import CodeParser


class TestPythonParsing:
    def test_parse_python_functions_and_classes(self):
        code = """
import os
from typing import List

class UserService:
    def get_user(self, user_id: str) -> dict:
        return {"id": user_id}

def calculate_total(items: List[int]) -> int:
    return sum(items)
"""
        result = CodeParser.parse_file("service.py", code)
        assert len(result["classes"]) >= 1
        assert any(c["name"] == "UserService" for c in result["classes"])
        assert any(f["name"] == "calculate_total" for f in result["functions"])
        assert len(result["imports"]) >= 2

    def test_parse_python_routes(self):
        code = """
from fastapi import APIRouter

router = APIRouter()

@router.get("/users")
def list_users():
    return []

@router.post("/users")
def create_user():
    return {}
"""
        result = CodeParser.parse_file("routes.py", code)
        assert len(result["routes"]) == 2
        methods = {r["method"] for r in result["routes"]}
        assert "GET" in methods
        assert "POST" in methods


class TestTypeScriptParsing:
    def test_parse_ts_functions_exports_and_components(self):
        code = """
import React, { useState } from 'react';
import { Button } from '@/components/ui/button';

export interface UserProfile {
    id: string;
    name: string;
}

export function UserDashboard() {
    return <div>Dashboard</div>;
}

export const fetchUsers = async () => {
    return [];
};
"""
        result = CodeParser.parse_file("UserDashboard.tsx", code)
        assert "UserDashboard" in result["components"] or any(f["name"] == "UserDashboard" for f in result["functions"])
        assert any(c["name"] == "UserProfile" for c in result["classes"])
        assert len(result["imports"]) >= 1


class TestGoParsing:
    def test_parse_go_package_functions_structs(self):
        code = """
package main

import (
    "fmt"
    "net/http"
)

type ServerConfig struct {
    Port int
    Host string
}

type Handler interface {
    ServeHTTP(w http.ResponseWriter, r *http.Request)
}

func StartServer(cfg ServerConfig) error {
    return nil
}

func handleHealth(w http.ResponseWriter, r *http.Request) {
    fmt.Fprintln(w, "OK")
}
"""
        result = CodeParser.parse_file("main.go", code)
        assert any("package:main" in imp for imp in result["imports"])
        assert any(f["name"] == "StartServer" for f in result["functions"])
        assert any(f["name"] == "handleHealth" for f in result["functions"])
        assert any(c["name"] == "ServerConfig" for c in result["classes"])
        assert any(c["name"] == "Handler" for c in result["classes"])

    def test_parse_go_routes(self):
        code = """
package main

func setupRoutes(r *gin.Engine) {
    r.GET("/api/v1/health", healthCheck)
    r.POST("/api/v1/users", createUser)
}
"""
        result = CodeParser.parse_file("routes.go", code)
        assert len(result["routes"]) >= 2
        paths = [r["path"] for r in result["routes"]]
        assert "/api/v1/health" in paths
        assert "/api/v1/users" in paths


class TestRustParsing:
    def test_parse_rust_structs_enums_and_functions(self):
        code = """
use std::collections::HashMap;

pub struct Config {
    pub workers: usize,
}

pub enum LogLevel {
    Info,
    Warn,
    Error,
}

pub trait Service {
    fn run(&self);
}

pub fn initialize(config: Config) -> Result<(), String> {
    Ok(())
}

fn internal_worker() {
}
"""
        result = CodeParser.parse_file("lib.rs", code)
        assert any(f["name"] == "initialize" for f in result["functions"])
        assert any(f["name"] == "internal_worker" for f in result["functions"])
        assert any(c["name"] == "Config" for c in result["classes"])
        assert any(c["name"] == "LogLevel" for c in result["classes"])
        assert any(c["name"] == "Service" for c in result["classes"])


class TestJavaParsing:
    def test_parse_java_class_methods_and_routes(self):
        code = """
package com.example.demo;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class UserController {

    @GetMapping("/api/users")
    public List<User> getAllUsers() {
        return List.of();
    }

    public void processData() {
    }
}
"""
        result = CodeParser.parse_file("UserController.java", code)
        assert any(c["name"] == "UserController" for c in result["classes"])
        assert any(f["name"] == "getAllUsers" for f in result["functions"])
        assert any(r["path"] == "/api/users" for r in result["routes"])
        assert len(result["imports"]) >= 2


class TestCppParsing:
    def test_parse_cpp_classes_and_functions(self):
        code = """
#include <iostream>
#include <vector>

namespace math {

class Matrix {
public:
    int rows;
    int cols;
};

int multiply(int a, int b) {
    return a * b;
}

}
"""
        result = CodeParser.parse_file("matrix.cpp", code)
        assert any(c["name"] == "Matrix" for c in result["classes"])
        assert any(c["name"] == "math" for c in result["classes"])
        assert any(f["name"] == "multiply" for f in result["functions"])
        assert any("iostream" in imp for imp in result["imports"])


class TestParserSafetyGuards:
    def test_empty_content_returns_empty_structure(self):
        result = CodeParser.parse_file("test.py", "")
        assert result == CodeParser._empty()

    def test_unknown_extension_returns_empty(self):
        result = CodeParser.parse_file("test.xyz", "content here")
        assert result == CodeParser._empty()

    def test_oversized_file_handled_safely(self):
        # Oversized string > 2MB
        huge_code = "def foo(): pass\n" * 150000
        result = CodeParser.parse_file("huge.py", huge_code)
        assert result == {"functions": [], "classes": [], "imports": [], "routes": [], "models": []}
