def get_answer_stream_ollama(
    self, question: str, mode: str = 'video', context: str = None, deep_thinking: bool = False
):
    """使用Ollama获取问题的答案（流式响应）"""
    import json
    import re

    import requests

    if mode == 'video' and not context:
        if not self.is_initialized or len(self.subtitles) == 0:
            yield "视频知识库未初始化，请先上传视频并等待处理完成"
            return

        # 搜索相关片段
        segments = self.search_similar_segments(question, top_k=3)

        if not segments:
            yield "未找到与问题相关的视频内容"
            return

        # 构建上下文
        context = "\n\n".join(
            [
                f"片段 {i+1}（{self._format_time(seg['start_time'])} - {self._format_time(seg['end_time'])}）: {seg['text']}"
                for i, seg in enumerate(segments)
            ]
        )

    # 构建提示词
    prompt = f"""你是一个教育助手。请回答用户的问题。

用户问题: {question}

请提供有帮助的回答。如果你不确定答案，请诚实地说明。"""

    if mode == 'video':
        prompt = f"""你是一个教育视频内容助手。请根据以下视频内容片段回答用户的问题。

视频内容片段:
{context}

用户问题: {question}

请根据提供的视频内容片段回答问题。如果视频内容中没有足够的信息来回答问题，请说明这一点。"""

    logger.info(f"构建的提示词: {prompt[:100]}...")

    # 根据深度思考模式调整系统提示词
    system_prompt = "你是一个教育助手，请始终使用中文回答问题。"
    if deep_thinking:
        system_prompt += """你必须按照以下格式回答：
1. 首先，在<think>标签内详细分析问题并展示你的思考过程
2. 然后，在标签外给出最终答案

例如：
<think>
首先，我需要理解问题的核心...
分析可能的解决方案...
考虑各种因素...
</think>

基于以上思考，我的回答是...

这个格式是强制性的，你必须将所有思考过程放在<think>标签内。
不要在回答中介绍自己，直接回答问题。"""
    else:
        system_prompt += "请直接给出简洁明了的回答，无需展示思考过程。"

    # 根据深度思考模式选择不同的模型
    if deep_thinking:
        model_to_use = "deepseek-r1:8b"  # 深度思考模式使用 deepseek-r1:8b
        logger.info(f"使用深度思考模式，选择模型: {model_to_use}")
    else:
        model_to_use = "qwen2.5:7b"  # 普通模式使用 qwen2.5:7b
        logger.info(f"使用普通模式，选择模型: {model_to_use}")

    try:
        # 尝试先使用非流式API获取回答
        try:
            logger.info("尝试使用非流式API获取回答")
            payload_non_stream = {"model": model_to_use, "prompt": prompt, "system": system_prompt, "stream": False}

            non_stream_response = requests.post(f"{OLLAMA_BASE_URL}/generate", json=payload_non_stream, timeout=30)

            if non_stream_response.status_code == 200:
                response_data = non_stream_response.json()
                if 'response' in response_data:
                    answer = response_data['response']
                    logger.info(f"非流式API成功获取回答，长度: {len(answer)}")

                    # 处理深度思考模式的回答
                    if deep_thinking:
                        # 提取思考过程和最终答案
                        think_matches = re.findall(r'<think>(.*?)</think>', answer, re.DOTALL)
                        if think_matches:
                            # 合并所有思考过程
                            thinking_process = "\n\n".join([match.strip() for match in think_matches])
                            # 移除所有思考标签及其内容
                            final_answer = re.sub(r'<think>.*?</think>', '', answer, flags=re.DOTALL).strip()

                            # 格式化为HTML，使思考过程可折叠
                            formatted_answer = f"""<details>
<summary>思考过程（点击展开）</summary>
<p>{thinking_process}</p>
</details>

{final_answer}"""
                            yield formatted_answer
                            return
                        else:
                            # 检查是否使用了其他格式的思考过程
                            analysis_match = re.search(
                                r'(?:1\.?\s*\*\*分析问题\*\*：|分析问题：)(.*?)(?:2\.|\*\*思考|$)', answer, re.DOTALL
                            )
                            thinking_match = re.search(
                                r'(?:2\.?\s*\*\*思考过程\*\*：|思考过程：)(.*?)(?:3\.|\*\*解决|$)', answer, re.DOTALL
                            )
                            solution_match = re.search(
                                r'(?:3\.?\s*\*\*解决方案\*\*：|解决方案：)(.*?)(?:最终答案|$)', answer, re.DOTALL
                            )

                            if analysis_match or thinking_match or solution_match:
                                # 提取思考部分
                                thinking_parts = []
                                if analysis_match:
                                    thinking_parts.append(f"**分析问题**：{analysis_match.group(1).strip()}")
                                if thinking_match:
                                    thinking_parts.append(f"**思考过程**：{thinking_match.group(1).strip()}")
                                if solution_match:
                                    thinking_parts.append(f"**解决方案**：{solution_match.group(1).strip()}")

                                thinking_process = "\n\n".join(thinking_parts)

                                # 提取最终答案
                                final_answer_match = re.search(
                                    r'(?:最终答案：|最终答案:|最终答案|最后答案：|最后答案:|最后答案)(.*?)$',
                                    answer,
                                    re.DOTALL,
                                )
                                if final_answer_match:
                                    final_answer = final_answer_match.group(1).strip()
                                else:
                                    # 如果没有明确的最终答案标记，尝试提取最后一段作为答案
                                    paragraphs = answer.split('\n\n')
                                    final_answer = paragraphs[-1].strip()
                                    # 如果最后一段包含分析/思考/解决方案，则使用一个通用回答
                                    if re.search(r'分析|思考|解决方案', final_answer):
                                        final_answer = "根据以上分析，我的回答是：" + re.sub(
                                            r'.*?(您好|你好).*', '您好！我是教育助手，请问有什么可以帮助您的？', answer
                                        )

                                # 格式化为HTML，使思考过程可折叠
                                formatted_answer = f"""<details>
<summary>思考过程（点击展开）</summary>
<p>{thinking_process}</p>
</details>

{final_answer}"""
                                yield formatted_answer
                                return

                    yield answer
                    return
                else:
                    logger.warning("非流式API返回成功但没有response字段")
            else:
                logger.warning(f"非流式API请求失败: {non_stream_response.status_code}")
        except Exception as e:
            logger.warning(f"非流式API请求出错: {str(e)}，将尝试流式API")

        # 如果非流式API失败，尝试流式API
        logger.info("尝试使用流式API获取回答")
        payload = {"model": model_to_use, "prompt": prompt, "system": system_prompt, "stream": True}

        logger.info(f"发送请求到Ollama API: {OLLAMA_BASE_URL}/generate，使用模型: {model_to_use}")

        # 如果没有收到响应，提供一个默认回答
        has_yielded = False
        start_time = time.time()
        timeout_seconds = 15  # 设置15秒超时

        try:
            with requests.post(
                f"{OLLAMA_BASE_URL}/generate", json=payload, stream=True, timeout=timeout_seconds
            ) as response:
                logger.info(f"Ollama API响应状态码: {response.status_code}")

                if response.status_code != 200:
                    logger.error(f"Ollama API返回错误: {response.status_code}, 响应内容: {response.text}")
                    yield f"Ollama API返回错误: {response.status_code}。请检查Ollama服务是否正常运行，或尝试使用在线模式。"
                    return

                logger.info(f"Ollama API返回成功，开始处理流式响应")

                # 创建一个缓冲区来收集完整的响应
                complete_response = ""

                # 逐行读取流式响应
                line_count = 0
                for line in response.iter_lines():
                    line_count += 1
                    logger.info(f"处理响应行 #{line_count}")

                    if line:
                        try:
                            # 解析JSON响应
                            line_text = line.decode('utf-8')
                            logger.info(f"收到原始响应行: {line_text[:100]}...")
                            data = json.loads(line_text)

                            if 'response' in data:
                                chunk = data['response']
                                logger.info(f"收到Ollama响应片段: {chunk[:20]}...")
                                has_yielded = True

                                # 将当前块添加到完整响应中
                                complete_response += chunk

                                # 如果是深度思考模式，检查是否有完整的思考标签
                                if deep_thinking and "<think>" in complete_response and "</think>" in complete_response:
                                    # 检查是否有完整的思考标签对
                                    think_open_count = complete_response.count("<think>")
                                    think_close_count = complete_response.count("</think>")

                                    # 如果有完整的思考标签对
                                    if think_open_count > 0 and think_open_count == think_close_count:
                                        # 提取思考过程
                                        think_matches = re.findall(
                                            r'<think>(.*?)</think>', complete_response, re.DOTALL
                                        )
                                        if think_matches:
                                            # 合并所有思考过程
                                            thinking_process = "\n\n".join([match.strip() for match in think_matches])
                                            # 移除所有思考标签及其内容
                                            final_answer = re.sub(
                                                r'<think>.*?</think>', '', complete_response, flags=re.DOTALL
                                            ).strip()

                                            # 格式化为HTML，使思考过程可折叠
                                            formatted_response = f"""<details>
<summary>思考过程（点击展开）</summary>
<p>{thinking_process}</p>
</details>

{final_answer}"""
                                            yield formatted_response
                                            return

                                # 如果不是深度思考模式或没有完整的思考标签对，直接输出当前块
                                yield chunk
                            elif 'error' in data:
                                logger.error(f"Ollama返回错误: {data['error']}")
                                has_yielded = True
                                yield f"Ollama错误: {data['error']}。请检查Ollama服务是否正常运行，或尝试使用在线模式。"
                        except json.JSONDecodeError as e:
                            logger.error(f"无法解析JSON: {line}, 错误: {str(e)}")
                            continue

                        # 检查是否超时
                        if time.time() - start_time > timeout_seconds * 2:  # 给予两倍的超时时间
                            logger.error("Ollama响应处理超时")
                            if not has_yielded:
                                yield "处理请求超时，请检查Ollama服务是否正常运行，或尝试使用在线模式。"
                            return

                # 处理完整响应中的深度思考（如果流式处理没有处理）
                if deep_thinking and has_yielded and "<think>" in complete_response:
                    # 提取思考过程
                    think_matches = re.findall(r'<think>(.*?)</think>', complete_response, re.DOTALL)
                    if think_matches:
                        # 合并所有思考过程
                        thinking_process = "\n\n".join([match.strip() for match in think_matches])
                        # 移除所有思考标签及其内容
                        final_answer = re.sub(r'<think>.*?</think>', '', complete_response, flags=re.DOTALL).strip()

                        # 格式化为HTML，使思考过程可折叠
                        formatted_response = f"""<details>
<summary>思考过程（点击展开）</summary>
<p>{thinking_process}</p>
</details>

{final_answer}"""
                        yield formatted_response

            logger.info("Ollama流式响应结束")
        except requests.exceptions.Timeout:
            logger.error(f"Ollama API请求超时（{timeout_seconds}秒）")
            yield f"Ollama API请求超时（{timeout_seconds}秒）。请检查Ollama服务是否正常运行，或尝试使用在线模式。"
            return
        except requests.exceptions.ConnectionError:
            logger.error("无法连接到Ollama服务")
            yield "无法连接到Ollama服务。请确保Ollama服务正在运行，或尝试使用在线模式。"
            return

        # 如果没有收到任何响应，返回一个默认回答
        if not has_yielded:
            logger.warning("未收到Ollama任何响应，返回默认回答")
            yield "我是AI助手，很抱歉，我目前无法处理您的请求。这可能是因为Ollama模型对中文支持有限或服务不稳定。请尝试使用在线模式或联系管理员。"

    except Exception as e:
        logger.error(f"Ollama流式响应出错: {str(e)}")
        import traceback

        logger.error(traceback.format_exc())
        yield f"Ollama服务出错: {str(e)}。请检查Ollama服务是否正常运行，或尝试使用在线模式。"
