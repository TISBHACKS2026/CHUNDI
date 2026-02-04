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

    // Basic validation
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

        // Store Supabase access token
        localStorage.setItem("access_token", data.access_token);

        // Redirect to dashboard
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

async function get_usersAndtopic() {
    const token = localStorage.getItem("access_token");
    if (!token) {
        window.location.href = "/";
        return;
    }

    try {
        const res = await fetch("/api/get_topics", {
            headers: {
                "Authorization": "Bearer " + token
            }
        });

        if (!res.ok) {
            console.error(`Error: ${res.status} - ${res.statusText}`);  // Log for debugging
            window.location.href = "/";
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
        window.location.href = "/";
    }
}
