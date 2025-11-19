# AI Funland LLM Q&A Platform

## Overview

A modular LLM Q&A platform with OpenVINO acceleration, ModelScope model management, bilingual UI, and one-click startup on Windows.

## Features

- Q&A Web UI with model selection
- Model management: download, FP16/INT8 quantization, delete
- System panel: CPU/GPU, memory, accelerator selection
- i18n: English/中文
- Python backend with APIFlask
- OpenVINO and OpenVINO GenAI integration
- ModelScope SDK downloader with progress and resume
- Request queue and concurrency handling

## Installation

- Double-click `start.bat`
- The script prepares Python, installs dependencies, starts the server, opens the browser

## Usage

- Open `http://127.0.0.1:8000`
- Select device and model
- Enter prompt, click Send
- Manage models in the Model Management panel

## Contributing

- Fork, create branch, send PR

## License

- Apache-2.0

---

# AI Funland LLM 问答平台

## 概述

一个模块化的 LLM 问答平台，集成 OpenVINO 加速、ModelScope 模型管理、双语界面，以及 Windows 一键启动。

## 功能特性

- 问答 Web 界面，支持模型选择
- 模型管理：下载、FP16/INT8 量化、删除
- 系统面板：CPU/GPU、内存、加速器选择
- 国际化：中英文切换
- 后端 Python，基于 APIFlask
- 集成 OpenVINO 与 OpenVINO GenAI
- ModelScope 官方 SDK 下载器，进度与断点续传
- 请求队列与并发处理

## 安装

- 双击 `start.bat`
- 脚本准备 Python、安装依赖、启动服务并打开浏览器

## 使用说明

- 访问 `http://127.0.0.1:8000`
- 选择设备与模型
- 输入提示词并点击发送
- 在模型管理面板进行模型下载、量化与删除

## 贡献指南

- Fork 仓库，创建分支，提交 PR

## 许可证

- Apache-2.0