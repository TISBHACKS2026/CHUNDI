async function sendLogin() {
    const email = document.getElementById("email").value;
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;
    const errorDiv = document.getElementById("error");

    errorDiv.textContent = "";

    if (!email.trim() || !username.trim() || !password.trim()) {
        errorDiv.textContent = "Please fill in all fields";
        return;
    }

    if (password.length < 6) {
        errorDiv.textContent = "Password must be at least 6 characters";
        return;
    }

    try {
        const response = await fetch("/api/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, username, password })
        });

        const data = await response.json();

        if (!response.ok || data.error) {
            errorDiv.textContent = data.error || "Invalid username/password";
            return;
        }

        localStorage.setItem("access_token", data.access_token);
        window.location.href = "/dashboard";

    } catch (err) {
        console.error(err);
        errorDiv.textContent = "Server unreachable";
    }
}

async function sendSignup() {
    const email = document.getElementById("email").value.trim();
    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value;
    const errorDiv = document.getElementById("error");

    errorDiv.textContent = "";


    if (!email || !username || !password) {
        errorDiv.textContent = "All fields are required";
        return;
    }

    if (password.length < 6) {
        errorDiv.textContent = "Password must be at least 6 characters";
        return;
    }

    try {
        const response = await fetch("/api/signup", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                email: email,
                username: username,
                password: password
            })
        });

        const data = await response.json();

        if (!response.ok || data.error) {
            errorDiv.textContent = data.error || "Signup failed";
            return;
        }


        localStorage.setItem("access_token", data.access_token);


        window.location.href = "/dashboard";

    } catch (err) {
        console.error(err);
        errorDiv.textContent = "Server unreachable";
    }
}


async function loadUser() {
    const token = localStorage.getItem("access_token");
    if (!token) {
        window.location.href = "/";
        return;
    }

    try {
        const res = await fetch("/api/me", {
            headers: {
                "Authorization": "Bearer " + token
            }
        });

        if (!res.ok) {
            window.location.href = "/";
            return;
        }

        const data = await res.json();
        document.getElementById("welcome-text").textContent =
            `Welcome, ${data.display_name}!`;

    } catch (err) {
        console.error(err);
        window.location.href = "/";
    }
}

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('collapsed');
}


async function uploadFile() {
    const fileInput = document.querySelector('.file-input');
    const button = document.querySelector('.upload-btn');

    if (!fileInput.files || fileInput.files.length === 0) {
        alert('Please select a file first!');
        return;
    }

    const accessToken = localStorage.getItem("access_token");
    if (!accessToken) {
        alert("Please log in first!");
        window.location.href = "/";
        return;
    }

    const file = fileInput.files[0];
    const originalText = button.textContent;
    button.textContent = 'Uploading...';
    button.disabled = true;

    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch('/api/upload', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${accessToken}`
            },
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json();
            console.error(errorData);
        }

        const result = await response.json();
        alert(`Upload successful! Extracted topic: ${result.topic}`);

        fileInput.value = '';

    } catch (error) {
        console.error('Error:', error);
        alert(`Upload failed: ${error.message}`);
    } finally {
        button.textContent = originalText;
        button.disabled = false;
    }
}

async function get_usersAndtopic(api) {
    const token = localStorage.getItem("access_token");
    if (!token) {
        window.location.href = "/dashboard";
        return;
    }

    try {
        const res = await fetch(api, {
            headers: {
                "Authorization": "Bearer " + token
            }
        });

        if (!res.ok) {
            console.error(`Error: ${res.status} - ${res.statusText}`); 
            window.location.href = "/dashboard";
            return;
        }

        const data = await res.json();
        const container = document.getElementById("topics-container");
        container.innerHTML = "";

        data.result_topics.forEach((topicObj, index) => {
            const topic = topicObj.topic;
            const content = data.result_content[index]?.content ?? "";

            const wrapper = document.createElement("div");
            wrapper.style.width = "80%";
            wrapper.style.margin = "12px auto";
            wrapper.style.borderRadius = "8px";
            wrapper.style.background = "#fff";
            wrapper.style.boxShadow = "0 2px 6px rgba(0,0,0,0.1)";

            const button = document.createElement("button");
            button.textContent = topic;
            button.style.width = "100%";
            button.style.padding = "14px";
            button.style.fontSize = "1.1rem";
            button.style.textAlign = "left";
            button.style.border = "none";
            button.style.background = "transparent";
            button.style.cursor = "pointer";
            button.style.fontWeight = "600";

            const contentDiv = document.createElement("div");
            contentDiv.style.display = "none";
            contentDiv.style.padding = "14px";
            contentDiv.style.borderTop = "1px solid #ddd";

            const pre = document.createElement("pre");
            pre.textContent = content;
            pre.style.whiteSpace = "pre-wrap";
            pre.style.margin = "0";

            contentDiv.appendChild(pre);

            button.onclick = () => {
                const isOpen = contentDiv.style.display === "block";
                contentDiv.style.display = isOpen ? "none" : "block";
            };

            wrapper.appendChild(button);
            wrapper.appendChild(contentDiv);
            container.appendChild(wrapper);
        });




    } catch (err) {
        console.error(err);
        window.location.href = "/dashboard";
    }
}

let currentTopicId = null;
let chatHistory = [];
let currentChatId = null;
async function loadChatTopics() {
    const token = localStorage.getItem("access_token");
    if (!token) {
        window.location.href = "/dashboard";
        return;
    }

    try {
        const res = await fetch("/api/chat/topics", {
            headers: {
                "Authorization": "Bearer " + token
            }
        });

        if (!res.ok) {
            console.error("Failed to load topics");
            return;
        }

        const data = await res.json();
        renderTopicSelector(data.topics);
    } catch (err) {
        console.error(err);
    }
}

function renderTopicSelector(topics) {
    const container = document.getElementById("topics-container");
    if (!container) return;

    container.innerHTML = `
        <div style="margin-bottom: 20px;">
            <label for="topic-select" style="font-weight: 600; margin-right: 10px;">Select Topic:</label>
            <select id="topic-select" style="padding: 8px; border-radius: 4px; border: 1px solid #ccc;">
                <option value="">Start general discussion</option>
                ${topics.map(topic => 
                    `<option value="${topic.id}">${topic.topic}</option>`
                ).join('')}
            </select>
        </div>
        <div id="chat-messages" style="
            height: 400px;
            overflow-y: auto;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            background: white;
        "></div>
        <div style="display: flex; gap: 10px;">
            <input type="text" id="chat-input" placeholder="Type your message..." style="
                flex: 1;
                padding: 12px;
                border: 1px solid #ccc;
                border-radius: 6px;
                font-size: 14px;
            " onkeypress="if(event.key === 'Enter') sendChatMessage()">
            <button onclick="sendChatMessage()" style="
                padding: 12px 24px;
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-size: 14px;
            ">Send</button>
        </div>
    `;

    document.getElementById("topic-select").addEventListener("change", function(e) {
        currentTopicId = e.target.value || null;
        clearChat();
    });
}

function clearChat() {
    chatHistory = [];
    const chatMessages = document.getElementById("chat-messages");
    if (chatMessages) {
        chatMessages.innerHTML = "";
    }
}

function addMessageToChat(sender, message, isUser) {
    const chatMessages = document.getElementById("chat-messages");
    if (!chatMessages) return;

    const messageDiv = document.createElement("div");
    messageDiv.style.marginBottom = "16px";
    messageDiv.style.padding = "12px";
    messageDiv.style.borderRadius = "8px";
    messageDiv.style.background = isUser ? "#e3f2fd" : "#f5f5f5";
    messageDiv.style.borderLeft = isUser ? "4px solid #2196f3" : "4px solid #4caf50";

    const senderDiv = document.createElement("div");
    senderDiv.style.fontWeight = "600";
    senderDiv.style.marginBottom = "4px";
    senderDiv.style.color = isUser ? "#1565c0" : "#2e7d32";
    senderDiv.textContent = sender;

    const messageContentDiv = document.createElement("div");
    messageContentDiv.style.whiteSpace = "pre-wrap";
    messageContentDiv.style.fontSize = "14px";
    messageContentDiv.style.lineHeight = "1.5";
    messageContentDiv.textContent = message;

    messageDiv.appendChild(senderDiv);
    messageDiv.appendChild(messageContentDiv);


    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

async function sendChatMessage() {
    const input = document.getElementById("chat-input");
    const message = input.value.trim();
    if (!message) return;

    const token = localStorage.getItem("access_token");
    if (!token) {
        window.location.href = "/dashboard";
        return;
    }

    addMessageToChat("You", message, true);
    input.value = "";

    try {
        const response = await fetch("/api/chat/send", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + token
            },
            body: JSON.stringify({
                topic_id: currentTopicId,
                chat_id: currentChatId,
                message: message
            })
        });

        if (!response.ok) {
            throw new Error("Chat send failed");
        }

        const data = await response.json();

        if (!currentChatId) {
            currentChatId = data.chat_id;
        }
        addMessageToChat("AI Tutor", data.ai_response, false);

    } catch (err) {
        console.error(err);
        addMessageToChat(
            "System",
            "Error: failed to get AI response.",
            false
        );
    }
}

async function loadChatHistory(chatId) {
    const token = localStorage.getItem("access_token");
    if (!token || !chatId) return;

    try {
    const res = await fetch(`/api/chat/history/${chatId}`, {
            headers: {
                "Authorization": "Bearer " + token
            }
        });

        if (!res.ok) {
            throw new Error("Failed to load chat history");
        }

        const data = await res.json();

        clearChat();
        currentChatId = chatId;

        data.messages.forEach(msg => {
            addMessageToChat(
                msg.is_user ? "You" : "AI Tutor",
                msg.content,
                msg.is_user
            );
        });

    } catch (err) {
        console.error(err);
        addMessageToChat(
            "System",
            "Error: failed to load chat history.",
            false
        );
    }
}

function logout() {
    localStorage.removeItem("access_token");
    window.location.href = "/";
}

async function loadSettings() {
    const token = localStorage.getItem("access_token");
    if (!token) {
        window.location.href = "/";
        return;
    }

    try {
        const res = await fetch("/api/me", {
            headers: { "Authorization": "Bearer " + token }
        });

        if (!res.ok) {
            window.location.href = "/";
            return;
        }

        const user = await res.json();
        document.getElementById("email").value = user.email || "";
        document.getElementById("display-name").value = user.display_name || "";
    } catch (err) {
        console.error(err);
        window.location.href = "/";
    }
}


async function updateProfile() {
    const displayName = document.getElementById("display-name").value;
    const notification = document.getElementById("profile-notification");

    if (!displayName.trim()) {
        showNotification(notification, "Display name cannot be empty", "error");
        return;
    }

    const token = localStorage.getItem("access_token");
    const btn = document.querySelector('.btn-save');
    const originalText = btn.textContent;
    btn.disabled = true;
    btn.textContent = "Saving...";

    try {
        const res = await fetch("/api/update-profile", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + token
            },
            body: JSON.stringify({ display_name: displayName })
        });

        const data = await res.json();

        if (res.ok) {
            showNotification(notification, "Profile updated!", "success");
        } else {
            showNotification(notification, data.error || "Update failed", "error");
        }
    } catch (err) {
        showNotification(notification, "Network error", "error");
    } finally {
        btn.disabled = false;
        btn.textContent = originalText;
    }
}

function showNotification(element, message, type) {
    element.textContent = message;
    element.className = `notification ${type}`;
    element.style.display = 'block';

    setTimeout(() => {
        element.style.display = 'none';
        }, 3000);
}

async function loadDashboardStats() {
    const token = localStorage.getItem("access_token");
    if (!token) return;

    try {
        const topicsRes = await fetch("/api/chat/topics", {
            headers: { "Authorization": "Bearer " + token }
        });

        if (topicsRes.ok) {
            const topicsData = await topicsRes.json();
            document.getElementById("doc-count").textContent = topicsData.topics?.length || 0;
            document.getElementById("topic-count").textContent = topicsData.topics?.length || 0;
        }

        const statsRes = await fetch("/api/dashboard/stats", {
            headers: { "Authorization": "Bearer " + token }
        });

        if (statsRes.ok) {
            const statsData = await statsRes.json();
            document.getElementById("chat-count").textContent = statsData.chat_count || 0;
            document.getElementById("week-count").textContent = statsData.week_count || 0;
        }
    } catch (err) {
        console.error("Error loading stats:", err);
    }
}

let allChatSessions = [];

function toggleChatSidebar() {
    const sidebar = document.getElementById('chat-sidebar');
    sidebar.classList.toggle('collapsed');
}

function startNewChat() {
    currentChatId = null;
    currentTopicId = null;
    clearChat();
    loadChatTopics();
}

async function loadAllChats() {
    const token = localStorage.getItem("access_token");
    if (!token) {
        window.location.href = "/";
        return;
    }

    try {
        const response = await fetch("/api/dashboard/stats", {
            headers: { "Authorization": "Bearer " + token }
        });
        const chatListDiv = document.getElementById("chat-list");
        const topicsRes = await fetch("/api/chat/topics", {
            headers: { "Authorization": "Bearer " + token }
        });

        if (topicsRes.ok) {
            const topicsData = await topicsRes.json();
            const topics = topicsData.topics || [];

            chatListDiv.innerHTML = "";

            if (topics.length === 0) {
                chatListDiv.innerHTML = `
                           <div style="padding: 20px; text-align: center; color: #999;">
                               No chats yet.<br>Upload a document to get started!
                           </div>
                       `;
                return;
            }
            for (const topic of topics) {
                const chatsRes = await fetch(`/api/chat/list/${topic.id}`, {
                    headers: { "Authorization": "Bearer " + token }
                });

                if (chatsRes.ok) {
                    const chatsData = await chatsRes.json();
                    const chatIds = chatsData.chats || [];

                    chatIds.forEach(chatId => {
                        const chatItem = document.createElement("div");
                        chatItem.className = "chat-item";
                        chatItem.onclick = () => loadChatById(chatId, topic.id);

                        chatItem.innerHTML = `
                                   <div class="chat-item-title">${topic.topic}</div>
                                   <div class="chat-item-preview">Chat session</div>
                                   <div class="chat-item-time">Click to load</div>
                               `;

                        chatListDiv.appendChild(chatItem);
                    });
                }
            }

            if (chatListDiv.children.length === 0) {
                chatListDiv.innerHTML = `
                           <div style="padding: 20px; text-align: center; color: #999;">
                               No chats yet.<br>Start a conversation!
                           </div>
                       `;
            }
        }
    } catch (err) {
        console.error("Error loading chats:", err);
    }
}

async function loadChatById(chatId, topicId) {
    currentChatId = chatId;
    currentTopicId = topicId;
    document.querySelectorAll('.chat-item').forEach(item => {
        item.classList.remove('active');
    });
    event.currentTarget.classList.add('active');
    if (!document.getElementById("chat-messages")) {
        await loadChatTopics();
    }
    await loadChatHistory(chatId);
}
