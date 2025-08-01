import os
import subprocess
import json
import time
import select
import logging
import pty
import fcntl
from flask import Flask, request, jsonify

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Global variable to store Gemini CLI process
gemini_process = None

# Global variable to store current working directory
current_working_directory = os.getcwd()

# Global variable to store the single persistent Gemini CLI session
persistent_gemini_session = None


def start_gemini_cli():
    """Start the Gemini CLI process if not already running"""
    global gemini_process
    if gemini_process is None or gemini_process.poll() is not None:
        try:
            # Start gemini CLI in interactive mode
            gemini_process = subprocess.Popen(
                ['gemini'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0
            )
            logging.info("Gemini CLI started successfully")
            return True
        except Exception as e:
            logging.error(f"Failed to start Gemini CLI: {e}")
            return False
    return True


def configure_gemini_api_key(api_key):
    """Configure Gemini API key"""
    try:
        # Create .gemini directory if it doesn't exist
        gemini_dir = os.path.expanduser('~/.gemini')
        os.makedirs(gemini_dir, exist_ok=True)

        # Create settings.json with API key
        settings_file = os.path.join(gemini_dir, 'settings.json')
        settings = {
            "apiKey": api_key
        }

        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=2)

        logging.info("Gemini API key configured successfully")
        return True
    except Exception as e:
        logging.error(f"Failed to configure API key: {e}")
        return False


def get_configured_api_key():
    """Get the configured API key from settings file"""
    try:
        gemini_dir = os.path.expanduser('~/.gemini')
        settings_file = os.path.join(gemini_dir, 'settings.json')

        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                settings = json.load(f)
                return settings.get('apiKey')
    except Exception as e:
        logging.error(f"Failed to read API key from settings: {e}")
    return None


def test_gemini_authentication(api_key=None):
    """Test Gemini CLI authentication with the provided API key"""
    if not api_key:
        api_key = get_configured_api_key()

    if not api_key:
        logging.error("No API key available for authentication test")
        return False

    try:
        # Set up environment for testing
        env = os.environ.copy()
        env['GEMINI_API_KEY'] = api_key.strip()
        env['GEMINI_DEFAULT_AUTH_TYPE'] = 'gemini-api-key'
        env['GOOGLE_GENAI_USE_GEMINI'] = 'true'
        env['GEMINI_DISABLE_AUTH_PROMPT'] = 'true'
        env['GEMINI_NON_INTERACTIVE'] = 'true'

        # Test with a simple version command
        logging.info("Testing Gemini CLI authentication...")
        result = subprocess.run(
            ['gemini', '--version'],
            env=env,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            logging.info("✅ Gemini CLI authentication test passed")
            return True
        else:
            logging.error(f"❌ Gemini CLI authentication test failed. Return code: {result.returncode}")
            logging.error(f"Error output: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        logging.error("❌ Gemini CLI authentication test timed out")
        return False
    except Exception as e:
        logging.error(f"❌ Gemini CLI authentication test failed with exception: {e}")
        return False


def get_or_create_persistent_gemini_session(api_key=None):
    """Get or create the single persistent Gemini CLI session for this container"""
    global persistent_gemini_session

    logging.info(f"get_or_create_persistent_gemini_session called with api_key={'***' if api_key else None}")

    # Check if existing session is still alive
    if persistent_gemini_session and persistent_gemini_session['process'].poll() is None:
        logging.info("Reusing existing persistent Gemini session")
        persistent_gemini_session['last_used'] = time.time()
        return persistent_gemini_session

    # Create new session
    try:
        logging.info("Creating new persistent Gemini CLI session")
        # Set up environment with API key
        env = os.environ.copy()

        if not api_key:
            logging.info("No API key provided, trying to get configured API key")
            api_key = get_configured_api_key()

        if not api_key:
            logging.error("No API key available - cannot create Gemini session")
            logging.error("Please set GEMINI_API_KEY environment variable or configure via /configure endpoint")
            return None

        # 验证 API key 格式
        if not api_key.strip():
            logging.error("API key is empty or contains only whitespace")
            return None

        # 首先测试认证是否正常工作
        logging.info("Testing authentication before creating persistent session...")
        if not test_gemini_authentication(api_key):
            logging.error("Authentication test failed, cannot create persistent session")
            return None

        logging.info("API key available, setting up environment for automatic authentication")
        # 设置完整的环境变量以确保自动认证
        env['GEMINI_API_KEY'] = api_key.strip()
        # 强制指定默认认证类型为 gemini-api-key (API key)
        env['GEMINI_DEFAULT_AUTH_TYPE'] = 'gemini-api-key'
        # 确保非交互模式下使用API密钥
        env['GOOGLE_GENAI_USE_GEMINI'] = 'true'
        # 禁用交互式认证提示
        env['GEMINI_DISABLE_AUTH_PROMPT'] = 'true'
        # 设置非交互模式
        env['GEMINI_NON_INTERACTIVE'] = 'true'

        # Start Gemini CLI using pty for better TTY compatibility
        logging.info(f"Starting Gemini CLI process in directory: {current_working_directory}")
        logging.info("Environment variables set for automatic authentication:")
        logging.info(f"  GEMINI_API_KEY: {'***' if env.get('GEMINI_API_KEY') else 'Not set'}")
        logging.info(f"  GEMINI_DEFAULT_AUTH_TYPE: {env.get('GEMINI_DEFAULT_AUTH_TYPE', 'Not set')}")
        logging.info(f"  GOOGLE_GENAI_USE_GEMINI: {env.get('GOOGLE_GENAI_USE_GEMINI', 'Not set')}")

        # Use pty to create a pseudo-terminal for better Gemini CLI interaction
        master_fd, slave_fd = pty.openpty()

        process = subprocess.Popen(
            ['gemini'],  # Interactive mode with TTY
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            env=env,
            cwd=current_working_directory,
            preexec_fn=os.setsid  # Create new session
        )

        # Close slave fd in parent process
        os.close(slave_fd)

        # Make master fd non-blocking
        fcntl.fcntl(master_fd, fcntl.F_SETFL, os.O_NONBLOCK)

        # Wait for Gemini CLI to initialize
        logging.info("Waiting for Gemini CLI to initialize with automatic authentication...")
        time.sleep(2.0)  # Give time for Gemini CLI to initialize

        # Check if process started successfully
        if process.poll() is not None:
            logging.error(f"Gemini CLI process terminated immediately. Return code: {process.returncode}")
            # Try to read any error output
            try:
                if select.select([master_fd], [], [], 0.1)[0]:
                    error_output = os.read(master_fd, 4096).decode('utf-8', errors='ignore')
                    logging.error(f"Gemini CLI error output: {error_output}")
            except:
                pass
            os.close(master_fd)
            return None

        # With proper environment variables, Gemini CLI should authenticate automatically
        # Wait a bit more to ensure authentication completes
        time.sleep(3.0)

        # Verify the process is still running after authentication
        if process.poll() is not None:
            logging.error(f"Gemini CLI process died after initialization. Return code: {process.returncode}")
            # Try to read any error output
            try:
                if select.select([master_fd], [], [], 0.1)[0]:
                    error_output = os.read(master_fd, 4096).decode('utf-8', errors='ignore')
                    logging.error(f"Gemini CLI error output: {error_output}")
            except:
                pass
            os.close(master_fd)
            return None

        logging.info("Gemini CLI session created successfully with automatic authentication")

        persistent_gemini_session = {
            'process': process,
            'master_fd': master_fd,
            'created_at': time.time(),
            'last_used': time.time()
        }

        logging.info(f"Created persistent Gemini CLI session successfully (PID: {process.pid})")
        return persistent_gemini_session

    except Exception as e:
        logging.error(f"Failed to create persistent Gemini CLI session: {e}")
        import traceback
        logging.error(f"Traceback: {traceback.format_exc()}")
        return None


def send_to_persistent_gemini_session(prompt, api_key=None, timeout=120):
    """Send a prompt to the persistent Gemini CLI session"""
    global persistent_gemini_session

    # Get or create the persistent session
    session = get_or_create_persistent_gemini_session(api_key)
    if not session:
        return {"error": "Failed to create Gemini CLI session. Please check API key."}

    try:
        process = session['process']
        master_fd = session['master_fd']
        session['last_used'] = time.time()

        logging.info(f"Sending prompt to Gemini CLI (PID: {process.pid}): {prompt[:50]}...")

        # Check if process is still alive before sending
        if process.poll() is not None:
            logging.error(f"Gemini CLI process (PID: {process.pid}) has died with return code: {process.returncode}")
            return {"error": "Gemini CLI process has died"}

        # Send prompt to the Gemini CLI process via pty (it maintains all context internally)
        try:
            prompt_bytes = (prompt + '\n').encode('utf-8')
            os.write(master_fd, prompt_bytes)
            logging.info("Prompt sent to Gemini CLI via pty, waiting for response...")
        except Exception as e:
            logging.error(f"Failed to send prompt to Gemini CLI: {e}")
            return {"error": f"Failed to send prompt: {str(e)}"}

        # Read response with timeout
        start_time = time.time()
        all_output = ""
        last_data_time = start_time
        stable_period = 0

        while time.time() - start_time < timeout:
            # Check if there's data to read from pty
            if select.select([master_fd], [], [], 0.5)[0]:
                try:
                    data = os.read(master_fd, 4096).decode('utf-8', errors='ignore')
                    if data:
                        all_output += data
                        last_data_time = time.time()
                        stable_period = 0
                        logging.info(f"Read data chunk ({len(data)} chars): {repr(data[:100])}...")

                        # 检查是否包含明确的结束标志
                        # Gemini CLI 通常在响应完成后会显示状态栏
                        if 'gemini-' in data and '% context left)' in data:
                            logging.info("Found Gemini status line, waiting for completion...")
                            # 等待一段时间确保没有更多输出
                            time.sleep(1.0)
                            # 再次检查是否有更多数据
                            if not select.select([master_fd], [], [], 0.5)[0]:
                                logging.info("No additional data after status line, response complete")
                                break

                except Exception as e:
                    logging.error(f"Error reading from Gemini CLI pty: {e}")
                    break
            else:
                # Check if process is still alive
                if process.poll() is not None:
                    logging.error(f"Gemini CLI process died during communication: {process.returncode}")
                    break

                # 如果有输出但一段时间没有新数据，增加稳定计数
                if all_output.strip():
                    stable_period += 1
                    # 如果稳定期超过10个周期（约5秒），认为响应完成
                    if stable_period > 10:
                        logging.info(f"No new data for {stable_period * 0.5} seconds, response likely complete")
                        break

                # 总体超时保护
                if time.time() - start_time > 30:
                    logging.info("Overall timeout reached, ending response collection")
                    break

        # 处理最终响应
        response = all_output.strip()
        lines_read = response.count('\n') + 1 if response else 0
        logging.info(f"Final response ({lines_read} lines, {len(response)} chars): {response[:200]}...")

        return {
            "response": response,
            "persistent": True,
            "context_maintained_by": "gemini_cli_internal",
            "lines_read": lines_read,
            "process_pid": process.pid
        }

    except Exception as e:
        logging.error(f"Error communicating with persistent Gemini session: {e}")
        return {"error": f"Session communication error: {str(e)}"}


def cleanup_persistent_gemini_session():
    """Clean up the persistent Gemini CLI session if it's dead"""
    global persistent_gemini_session

    if persistent_gemini_session and persistent_gemini_session['process'].poll() is not None:
        logging.info("Cleaning up dead persistent Gemini session")
        try:
            os.close(persistent_gemini_session['master_fd'])
        except:
            pass
        persistent_gemini_session = None


def create_interactive_gemini_session():
    """Create an interactive Gemini CLI session without auto-authentication"""
    global persistent_gemini_session

    try:
        logging.info("Creating interactive Gemini CLI session (no auto-auth)")

        # 清理现有会话
        cleanup_persistent_gemini_session()

        # 设置最小环境变量，不包含自动认证
        env = os.environ.copy()
        # 移除可能存在的自动认证环境变量
        env.pop('GEMINI_API_KEY', None)
        env.pop('GEMINI_DEFAULT_AUTH_TYPE', None)
        env.pop('GOOGLE_GENAI_USE_GEMINI', None)
        env.pop('GEMINI_DISABLE_AUTH_PROMPT', None)
        env.pop('GEMINI_NON_INTERACTIVE', None)

        # 启动 Gemini CLI 进程
        master_fd, slave_fd = pty.openpty()

        process = subprocess.Popen(
            ['gemini'],
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            env=env,
            cwd=current_working_directory,
            preexec_fn=os.setsid
        )

        os.close(slave_fd)

        # 设置非阻塞模式
        fcntl.fcntl(master_fd, fcntl.F_SETFL, os.O_NONBLOCK)

        # 等待初始输出
        time.sleep(3)

        # 读取初始欢迎信息
        initial_output = ""
        stable_count = 0
        max_wait_time = 10  # 最多等待10秒
        start_time = time.time()

        try:
            while time.time() - start_time < max_wait_time:
                if select.select([master_fd], [], [], 0.5)[0]:
                    data = os.read(master_fd, 4096).decode('utf-8', errors='ignore')
                    if data:
                        initial_output += data
                        stable_count = 0
                        logging.info(f"Interactive session initial data: {repr(data[:100])}...")

                        # 检查是否包含认证提示
                        if 'How would you like to authenticate' in data or 'Get started' in data:
                            # 等待更多输出确保完整
                            time.sleep(1)
                            continue
                    else:
                        stable_count += 1
                        if stable_count >= 3:  # 1.5秒无新数据
                            break
                else:
                    stable_count += 1
                    if stable_count >= 3 and initial_output.strip():
                        break
        except Exception as e:
            logging.error(f"Error reading initial output: {e}")

        persistent_gemini_session = {
            'process': process,
            'master_fd': master_fd,
            'created': time.time(),
            'last_used': time.time(),
            'interactive': True,
            'initial_output': initial_output
        }

        logging.info(f"Interactive Gemini CLI session created successfully (PID: {process.pid})")
        logging.info(f"Initial output length: {len(initial_output)} chars")

        return persistent_gemini_session

    except Exception as e:
        logging.error(f"Failed to create interactive Gemini session: {e}")
        return None


def send_to_interactive_session(user_input, timeout=30):
    """Send input to the interactive Gemini CLI session and get response"""
    global persistent_gemini_session

    if not persistent_gemini_session or persistent_gemini_session['process'].poll() is not None:
        return {"error": "No active interactive session"}

    try:
        process = persistent_gemini_session['process']
        master_fd = persistent_gemini_session['master_fd']
        persistent_gemini_session['last_used'] = time.time()

        logging.info(f"Sending interactive input: {user_input[:50]}...")

        # 发送用户输入
        input_data = (user_input + '\n').encode('utf-8')
        os.write(master_fd, input_data)

        # 读取响应
        start_time = time.time()
        all_output = ""
        stable_period = 0

        while time.time() - start_time < timeout:
            if select.select([master_fd], [], [], 0.5)[0]:
                try:
                    data = os.read(master_fd, 4096).decode('utf-8', errors='ignore')
                    if data:
                        all_output += data
                        stable_period = 0
                        logging.info(f"Interactive response chunk ({len(data)} chars): {repr(data[:100])}...")

                        # 检查是否包含提示符或完成标志
                        if any(prompt in data for prompt in [
                            'How would you like to authenticate',
                            'Get started',
                            'Enter your choice',
                            'Please enter',
                            'Select an option',
                            '> ',
                            'gemini-',
                            '/app'
                        ]):
                            # 等待一下确保输出完整
                            time.sleep(1.5)
                            # 再次检查是否有更多输出
                            extra_wait = 0
                            while extra_wait < 3 and select.select([master_fd], [], [], 0.5)[0]:
                                extra_data = os.read(master_fd, 4096).decode('utf-8', errors='ignore')
                                if extra_data:
                                    all_output += extra_data
                                    logging.info(f"Extra data: {repr(extra_data[:50])}...")
                                extra_wait += 1
                            logging.info("Found prompt, response complete")
                            break

                except Exception as e:
                    logging.error(f"Error reading interactive response: {e}")
                    break
            else:
                if all_output.strip():
                    stable_period += 1
                    if stable_period > 8:  # 4秒无新数据
                        logging.info("No new data for 4 seconds, response complete")
                        break

                if process.poll() is not None:
                    logging.error("Interactive process died")
                    break

        response = all_output.strip()
        logging.info(f"Interactive response complete ({len(response)} chars)")

        return {
            "response": response,
            "interactive": True,
            "process_pid": process.pid
        }

    except Exception as e:
        logging.error(f"Error in interactive session communication: {e}")
        return {"error": f"Interactive session error: {str(e)}"}


def send_to_gemini(prompt, api_key=None, interactive=False):
    """Send a prompt to Gemini CLI and get response"""
    try:
        # Set up environment with API key
        env = os.environ.copy()

        # If no API key provided, try to get from configured settings
        if not api_key:
            api_key = get_configured_api_key()

        if api_key:
            env['GEMINI_API_KEY'] = api_key
        else:
            # No API key available
            return {"error": "API key required. Please configure API key first using /gemini/configure endpoint."}

        # Handle interactive mode for file operations and git commands
        if interactive:
            # For interactive commands in Docker, we still need to capture output
            # but we can add flags to auto-accept common prompts
            try:
                # Use YOLO mode (-y) to automatically accept all actions
                result = subprocess.run(
                    ['gemini', '-p', prompt, '-y'],
                    capture_output=True,
                    text=True,
                    timeout=120,
                    check=False,
                    env=env
                )

                # If YOLO mode fails, try standard mode with auto-input
                if result.returncode != 0 and 'Unknown arguments' in result.stderr:
                    result = subprocess.run(
                        ['gemini', '-p', prompt],
                        capture_output=True,
                        text=True,
                        timeout=120,
                        check=False,
                        env=env,
                        input='\n'.join(['1', 'yes', 'y', 'continue', ''])  # Auto-answer common prompts
                    )

                return {
                    "response": result.stdout.strip() if result.stdout else "Command completed",
                    "stderr": result.stderr.strip() if result.stderr else "",
                    "returncode": result.returncode,
                    "interactive": True
                }

            except Exception as e:
                return {"error": f"Interactive command failed: {str(e)}", "interactive": True}
        else:
            # Use gemini CLI with proper -p flag for prompt (non-interactive)
            result = subprocess.run(
                ['gemini', '-p', prompt],
                capture_output=True,
                text=True,
                timeout=120,  # 2 minute timeout
                check=False,
                env=env
            )

        if result.returncode == 0:
            response = result.stdout.strip()
            if response:
                return {"response": response}
            else:
                return {"response": "Gemini CLI returned empty response"}
        else:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            logging.error(f"Gemini CLI error: {error_msg}")

            # Check if it's an API key issue
            if "Auth method" in error_msg or "GEMINI_API_KEY" in error_msg:
                return {"error": "API key required. Please provide a valid Gemini API key."}

            return {"error": f"Gemini CLI error: {error_msg}"}

    except subprocess.TimeoutExpired:
        logging.error("Gemini CLI request timed out")
        return {"error": "Request timed out"}
    except Exception as e:
        logging.error(f"Error calling Gemini CLI: {e}")
        return {"error": str(e)}


@app.route('/gemini', methods=['POST'])
def gemini():
    """Send a prompt to Gemini CLI (backward compatibility endpoint)"""
    data = request.get_json()
    if not data or 'prompt' not in data:
        return jsonify({"error": "Invalid request. 'prompt' field is required."}), 400

    prompt = data['prompt']
    api_key = data.get('api_key')  # Optional API key override
    interactive = data.get('interactive', False)  # Support interactive mode

    # Send to Gemini CLI
    result = send_to_gemini(prompt, api_key, interactive)

    if "error" in result:
        return jsonify(result), 400
    else:
        return jsonify(result)


@app.route('/gemini/chat', methods=['POST'])
def gemini_chat():
    """Send a prompt to Gemini CLI"""
    data = request.get_json()
    if not data or 'prompt' not in data:
        return jsonify({"error": "Invalid request. 'prompt' field is required."}), 400

    prompt = data['prompt']
    api_key = data.get('api_key')  # Optional API key override
    interactive = data.get('interactive', False)  # Support interactive mode

    # Send to Gemini CLI
    result = send_to_gemini(prompt, api_key, interactive)

    if "error" in result:
        return jsonify(result), 400
    else:
        return jsonify(result)


@app.route('/gemini/interactive', methods=['POST'])
def gemini_interactive():
    """Send an interactive prompt to Gemini CLI (for file operations, git commands, etc.)"""
    data = request.get_json()
    if not data or 'prompt' not in data:
        return jsonify({"error": "Invalid request. 'prompt' field is required."}), 400

    prompt = data['prompt']
    api_key = data.get('api_key')  # Optional API key override

    # Force interactive mode
    result = send_to_gemini(prompt, api_key, interactive=True)

    if "error" in result:
        return jsonify(result), 400
    else:
        return jsonify(result)


@app.route('/gemini/session', methods=['POST'])
def gemini_session():
    """Send a prompt to the persistent Gemini CLI session (maintains full chat history via Gemini CLI's internal memory)"""
    data = request.get_json()
    if not data or 'prompt' not in data:
        return jsonify({"error": "Invalid request. 'prompt' field is required."}), 400

    prompt = data['prompt']
    api_key = data.get('api_key')  # Optional API key override

    # Clean up dead session if any
    cleanup_persistent_gemini_session()

    # Send prompt to the single persistent session (Gemini CLI maintains all context)
    result = send_to_persistent_gemini_session(prompt, api_key)

    if "error" in result:
        return jsonify(result), 500
    else:
        return jsonify(result)


@app.route('/gemini/session/reset', methods=['POST'])
def reset_gemini_session():
    """Reset the persistent Gemini CLI session (starts fresh conversation)"""
    global persistent_gemini_session

    if persistent_gemini_session:
        try:
            persistent_gemini_session['process'].terminate()
        except:
            pass
        persistent_gemini_session = None
        return jsonify({"message": "Persistent Gemini CLI session reset successfully"})
    else:
        return jsonify({"message": "No active session to reset"})


@app.route('/gemini/session/status', methods=['GET'])
def gemini_session_status():
    """Get status of the persistent Gemini CLI session"""
    global persistent_gemini_session

    cleanup_persistent_gemini_session()  # Clean up first

    if persistent_gemini_session:
        return jsonify({
            "active": True,
            "created_at": persistent_gemini_session['created_at'],
            "last_used": persistent_gemini_session['last_used'],
            "alive": persistent_gemini_session['process'].poll() is None,
            "context_managed_by": "gemini_cli_internal"
        })
    else:
        return jsonify({
            "active": False,
            "context_managed_by": "gemini_cli_internal"
        })


@app.route('/environments/<env_id>/gemini/session/status', methods=['GET'])
def gemini_session_status_with_env():
    """Get status of the persistent Gemini CLI session"""
    try:
        if persistent_gemini_session and persistent_gemini_session['process'].poll() is None:
            return jsonify({
                "active": True,
                "alive": True,
                "process_pid": persistent_gemini_session['process'].pid,
                "last_used": persistent_gemini_session.get('last_used', 0)
            })
        else:
            return jsonify({
                "active": False,
                "alive": False,
                "process_pid": None,
                "last_used": None
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/environments/<string:env_id>/gemini/interactive', methods=['POST'])
def start_interactive_gemini_session(env_id):
    """Start an interactive Gemini CLI session (like real CLI experience)"""
    try:
        logging.info(f"Starting interactive session for environment: {env_id}")

        # 创建交互式会话，不设置自动认证环境变量
        session = create_interactive_gemini_session()
        if not session:
            return jsonify({"error": "Failed to create interactive Gemini CLI session"}), 500

        return jsonify({
            "message": "Interactive Gemini CLI session started",
            "process_pid": session['process'].pid,
            "interactive": True,
            "env_id": env_id
        })
    except Exception as e:
        logging.error(f"Error starting interactive session: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/environments/<string:env_id>/gemini/interactive/input', methods=['POST'])
def send_interactive_input(env_id):
    """Send input to the interactive Gemini CLI session"""
    try:
        logging.info(f"Sending input to interactive session for environment: {env_id}")
        data = request.get_json()
        if not data or 'input' not in data:
            return jsonify({"error": "Missing 'input' field"}), 400

        user_input = data['input']
        timeout = data.get('timeout', 30)

        # 发送用户输入到交互式会话
        response = send_to_interactive_session(user_input, timeout)
        response['env_id'] = env_id  # 添加环境 ID 到响应
        return jsonify(response)

    except Exception as e:
        logging.error(f"Error sending interactive input: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/environments/<string:env_id>/gemini/interactive/output', methods=['GET'])
def get_interactive_output(env_id):
    """Get the initial output from interactive Gemini CLI session"""
    try:
        logging.info(f"Getting output from interactive session for environment: {env_id}")
        if not persistent_gemini_session or not persistent_gemini_session.get('interactive'):
            return jsonify({"error": "No active interactive session"}), 400

        initial_output = persistent_gemini_session.get('initial_output', '')
        return jsonify({
            "output": initial_output,
            "interactive": True,
            "process_pid": persistent_gemini_session['process'].pid,
            "env_id": env_id
        })

    except Exception as e:
        logging.error(f"Error getting interactive output: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/gemini/configure', methods=['POST'])
def configure_gemini():
    """Configure Gemini API key"""
    try:
        data = request.get_json()
        if not data or 'api_key' not in data:
            return jsonify({"error": "Missing 'api_key' in request"}), 400

        api_key = data['api_key']
        if configure_gemini_api_key(api_key):
            return jsonify({"message": "API key configured successfully"})
        else:
            return jsonify({"error": "Failed to configure API key"}), 500

    except Exception as e:
        logging.error(f"Error in configure_gemini: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/gemini/status', methods=['GET'])
def gemini_status():
    """Check if Gemini CLI is running"""
    global gemini_process
    is_running = gemini_process is not None and gemini_process.poll() is None
    return jsonify({"gemini_running": is_running})


@app.route('/gemini/restart', methods=['POST'])
def restart_gemini():
    """Restart Gemini CLI"""
    global gemini_process
    if gemini_process is not None:
        try:
            gemini_process.terminate()
            gemini_process.wait()
        except:
            pass
        gemini_process = None

    success = start_gemini_cli()
    return jsonify({"restarted": success})


@app.route('/execute', methods=['POST'])
def execute_command():
    """Execute general shell commands with persistent working directory"""
    global current_working_directory

    data = request.get_json()
    if not data or 'command' not in data:
        return jsonify({"error": "Invalid request. 'command' field is required."}), 400

    command = data['command'].strip()

    try:
        # Handle cd command specially to update working directory
        if command.startswith('cd '):
            # Extract the target directory
            target_dir = command[3:].strip()

            # Handle relative paths
            if not os.path.isabs(target_dir):
                target_dir = os.path.join(current_working_directory, target_dir)

            # Normalize the path
            target_dir = os.path.normpath(target_dir)

            # Check if directory exists
            if os.path.isdir(target_dir):
                current_working_directory = target_dir
                return jsonify({
                    "stdout": f"Changed directory to: {current_working_directory}",
                    "stderr": "",
                    "returncode": 0,
                    "cwd": current_working_directory
                })
            else:
                return jsonify({
                    "stdout": "",
                    "stderr": f"cd: no such file or directory: {target_dir}",
                    "returncode": 1,
                    "cwd": current_working_directory
                })

        # Handle pwd command
        elif command == 'pwd':
            return jsonify({
                "stdout": current_working_directory,
                "stderr": "",
                "returncode": 0,
                "cwd": current_working_directory
            })

        # Execute other commands in the current working directory
        else:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=current_working_directory,
                check=False  # Do not raise exception for non-zero exit codes
            )
            return jsonify({
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "cwd": current_working_directory
            })

    except Exception as e:
        return jsonify({"error": str(e), "cwd": current_working_directory}), 500


# ==================== Git Integration Functions ====================

@app.route('/git/clone', methods=['POST'])
def git_clone():
    """Clone a Git repository"""
    data = request.get_json()
    if not data or 'repo_url' not in data:
        return jsonify({"error": "Invalid request. 'repo_url' field is required."}), 400

    repo_url = data['repo_url']
    target_dir = data.get('target_dir', './workspace')

    try:
        # Create workspace directory if it doesn't exist
        os.makedirs(target_dir, exist_ok=True)

        # Clone the repository
        result = subprocess.run(
            ['git', 'clone', repo_url, target_dir],
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode == 0:
            return jsonify({
                "message": "Repository cloned successfully",
                "target_dir": target_dir,
                "stdout": result.stdout
            })
        else:
            return jsonify({
                "error": "Git clone failed",
                "stderr": result.stderr,
                "returncode": result.returncode
            }), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/git/status', methods=['GET'])
def git_status():
    """Get Git status of the workspace"""
    workspace_dir = request.args.get('dir', './workspace')

    try:
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            cwd=workspace_dir,
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode == 0:
            return jsonify({
                "status": "success",
                "changes": result.stdout.strip().split('\n') if result.stdout.strip() else [],
                "has_changes": bool(result.stdout.strip())
            })
        else:
            return jsonify({
                "error": "Git status failed",
                "stderr": result.stderr
            }), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/git/add', methods=['POST'])
def git_add():
    """Add files to Git staging area"""
    data = request.get_json()
    workspace_dir = data.get('dir', './workspace')
    files = data.get('files', ['.'])  # Default to add all files

    try:
        cmd = ['git', 'add'] + files
        result = subprocess.run(
            cmd,
            cwd=workspace_dir,
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode == 0:
            return jsonify({
                "message": "Files added to staging area",
                "files": files
            })
        else:
            return jsonify({
                "error": "Git add failed",
                "stderr": result.stderr
            }), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/git/commit', methods=['POST'])
def git_commit():
    """Commit changes to Git repository"""
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({"error": "Invalid request. 'message' field is required."}), 400

    workspace_dir = data.get('dir', './workspace')
    commit_message = data['message']

    try:
        result = subprocess.run(
            ['git', 'commit', '-m', commit_message],
            cwd=workspace_dir,
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode == 0:
            return jsonify({
                "message": "Changes committed successfully",
                "commit_message": commit_message,
                "stdout": result.stdout
            })
        else:
            return jsonify({
                "error": "Git commit failed",
                "stderr": result.stderr
            }), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/git/push', methods=['POST'])
def git_push():
    """Push changes to remote repository"""
    data = request.get_json() or {}
    workspace_dir = data.get('dir', './workspace')
    branch = data.get('branch', 'main')

    try:
        result = subprocess.run(
            ['git', 'push', 'origin', branch],
            cwd=workspace_dir,
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode == 0:
            return jsonify({
                "message": "Changes pushed successfully",
                "branch": branch,
                "stdout": result.stdout
            })
        else:
            return jsonify({
                "error": "Git push failed",
                "stderr": result.stderr
            }), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/git/pull', methods=['POST'])
def git_pull():
    """Pull latest changes from remote repository"""
    data = request.get_json() or {}
    workspace_dir = data.get('dir', './workspace')

    try:
        result = subprocess.run(
            ['git', 'pull'],
            cwd=workspace_dir,
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode == 0:
            return jsonify({
                "message": "Repository updated successfully",
                "stdout": result.stdout
            })
        else:
            return jsonify({
                "error": "Git pull failed",
                "stderr": result.stderr
            }), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/files/list', methods=['GET'])
def list_files():
    """List files in the workspace directory"""
    workspace_dir = request.args.get('dir', './workspace')

    try:
        if not os.path.exists(workspace_dir):
            return jsonify({"files": [], "message": "Directory does not exist"})

        files = []
        for root, dirs, filenames in os.walk(workspace_dir):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                rel_path = os.path.relpath(file_path, workspace_dir)
                files.append(rel_path)

        return jsonify({
            "files": sorted(files),
            "directory": workspace_dir,
            "count": len(files)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/files/read', methods=['GET'])
def read_file():
    """Read content of a specific file"""
    file_path = request.args.get('path')
    workspace_dir = request.args.get('dir', './workspace')

    if not file_path:
        return jsonify({"error": "Missing 'path' parameter"}), 400

    try:
        full_path = os.path.join(workspace_dir, file_path)

        # Security check: ensure the file is within workspace
        if not os.path.abspath(full_path).startswith(os.path.abspath(workspace_dir)):
            return jsonify({"error": "Access denied: file outside workspace"}), 403

        if not os.path.exists(full_path):
            return jsonify({"error": "File not found"}), 404

        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return jsonify({
            "content": content,
            "file_path": file_path,
            "size": len(content)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/files/write', methods=['POST'])
def write_file():
    """Write content to a specific file"""
    data = request.get_json()
    if not data or 'path' not in data or 'content' not in data:
        return jsonify({"error": "Invalid request. 'path' and 'content' fields are required."}), 400

    file_path = data['path']
    content = data['content']
    workspace_dir = data.get('dir', './workspace')

    try:
        full_path = os.path.join(workspace_dir, file_path)

        # Security check: ensure the file is within workspace
        if not os.path.abspath(full_path).startswith(os.path.abspath(workspace_dir)):
            return jsonify({"error": "Access denied: file outside workspace"}), 403

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return jsonify({
            "message": "File written successfully",
            "file_path": file_path,
            "size": len(content)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "gemini_available": True})


if __name__ == '__main__':
    # Initialize Gemini CLI on startup
    logging.info("Starting agent service with Gemini CLI support...")
    start_gemini_cli()

    # Runs on port 5000 inside the container
    app.run(host='0.0.0.0', port=5000)
