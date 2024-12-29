// 专家匹配模块
$(document).ready(function () {
    $('#name-form').on('submit', function (e) {
        e.preventDefault();
        handleExpertSearch($(this));
    });
});

function handleExpertSearch(form) {
    $('#spinner-container').show();
    $('#result').hide();
    
    $.ajax({
        url: '/process',
        data: form.serialize(),
        type: 'POST',
        success: handleExpertResponse,
        error: handleError,
        complete: () => $('#spinner-container').hide()
    });
}

function handleExpertResponse(response) {
    if (response && response.summary) {
        $('#summary').text(response.summary);
        $('#facts').html(formatList(response.facts));
        $('#interest').html(formatList(response.interest));
        $('#letter').text(response.letter[0]);
        $('#result').fadeIn();
    } else {
        showError('获取数据失败');
    }
}

// 聊天功能
function toggleChat() {
    const chatWindow = document.getElementById('chatWindow');
    chatWindow.classList.toggle('minimized');
}

// ...existing chat functions...

// 微博招商功能
function handleRecruitmentResponse(response) {
    if (!response) {
        showError('获取数据失败');
        return;
    }
    
    $('#profile-pic').attr('src', getDefaultAvatar());
    $('#summary').text(response.summary);
    $('#facts').html(formatList(response.facts));
    $('#interest').html(formatList(response.interest));
    $('#letter').text(response.letter[0]);
    $('#result').fadeIn();
}

// 营销方案功能
function handleMarketingSubmit(e) {
    e.preventDefault();
    const data = {
        product: document.getElementById('product').value,
        target: document.getElementById('target').value,
        goal: document.getElementById('goal').value
    };
    submitMarketingPlan(data);
}

function submitMarketingPlan(data) {
    showLoading('正在生成营销方案...');
    
    fetch('/marketing/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(handleJsonResponse)
    .then(data => {
        if (data.conversation) {
            displayConversation(data.conversation);
            document.getElementById('marketing-result').style.display = 'block';
        }
    })
    .catch(handleError)
    .finally(hideLoading);
}

// ...existing marketing functions...

// 库存管理功能
function handleInventorySubmit(e) {
    e.preventDefault();
    const data = {
        product: document.getElementById('inv-product').value,
        city: document.getElementById('inv-city').value,
        current_stock: parseInt(document.getElementById('current-stock').value)
    };
    submitInventoryAnalysis(data);
}

function submitInventoryAnalysis(data) {
    showLoading('正在分析库存策略...');
    
    fetch('/inventory/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(handleJsonResponse)
    .then(updateInventoryResults)
    .catch(handleError)
    .finally(hideLoading);
}

// 修复库存分析功能
function updateInventoryResults(data) {
    if (!data || data.error) {
        showError(data.error || '分析失败');
        return;
    }

    // 更新各个部分的显示
    document.getElementById('weather-impact').innerHTML = formatFactors(data.factors.weather_impact);
    document.getElementById('social-trends').innerHTML = formatFactors(data.factors.social_trends);
    document.getElementById('seasonal-events').innerHTML = formatEvents(data.factors.seasonal_events);
    document.getElementById('inventory-strategy').innerHTML = formatStrategy(data.strategy);
    document.getElementById('logistics-plan').innerHTML = formatLogistics(data.logistics);
    
    // 显示结果区域
    document.getElementById('inventory-result').style.display = 'block';
}

// 新增格式化函数
function formatEvents(events) {
    if (!Array.isArray(events) || !events.length) {
        return '<p>暂无相关数据</p>';
    }
    return events.map(event => `
        <div class="event-item">
            <h4>${event.event}</h4>
            <p>${event.impact.join('<br>')}</p>
        </div>
    `).join('');
}

function formatStrategy(strategy) {
    if (!strategy) return '<p>暂无策略建议</p>';
    return `
        <ul class="strategy-list">
            <li><strong>建议库存水平:</strong> ${strategy.suggested_level}</li>
            <li><strong>补货时间点:</strong> ${strategy.reorder_time}</li>
            <li><strong>安全库存量:</strong> ${strategy.safety_stock}</li>
            <li><strong>其他建议:</strong> ${strategy.recommendations}</li>
        </ul>
    `;
}

function formatLogistics(logistics) {
    if (!logistics) return '<p>暂无物流方案</p>';
    return `
        <ul class="logistics-list">
            <li><strong>配送路线:</strong> ${logistics.routes}</li>
            <li><strong>运力分配:</strong> ${logistics.resources}</li>
            <li><strong>时效保障:</strong> ${logistics.timeliness}</li>
            <li><strong>成本优化:</strong> ${logistics.cost_optimization}</li>
        </ul>
    `;
}

// 智能客服功能
function sendChatbotMessage() {
    const input = document.getElementById('chatbot-input');
    const message = input.value.trim();
    if (!message) return;
    
    appendChatMessage('user', message);
    input.value = '';
    
    fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message })
    })
    .then(handleJsonResponse)
    .then(data => {
        if (data.response) {
            appendChatMessage('bot', data.response);
        }
    })
    .catch(handleError);
}

// 完善聊天功能
function appendChatMessage(type, content) {
    const messages = document.getElementById('chatbot-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;
    messageDiv.innerHTML = `
        <div class="message-content">
            <div class="message-text">${content}</div>
        </div>
    `;
    messages.appendChild(messageDiv);
    messages.scrollTop = messages.scrollHeight;
}

// 显示/隐藏加载动画
function showLoading(message = '处理中...') {
    const spinner = document.getElementById('spinner-container');
    spinner.querySelector('span').textContent = message;
    spinner.style.display = 'flex';
}

function hideLoading() {
    document.getElementById('spinner-container').style.display = 'none';
}

// 完善营销方案对话展示
function displayConversation(conversation) {
    const planContent = document.getElementById('plan-content');
    planContent.innerHTML = '';
    
    conversation.forEach(turn => {
        // 添加问题
        const questionDiv = document.createElement('div');
        questionDiv.className = 'decision-maker-message';
        questionDiv.innerHTML = `
            <div class="message-content">
                <div class="message-header">
                    <i class="fas fa-user"></i> 
                    回合 ${turn.round} - 问题
                </div>
                <div class="message-text">${turn.question}</div>
            </div>
        `;
        planContent.appendChild(questionDiv);
        
        // 添加回答
        const answerDiv = document.createElement('div');
        answerDiv.className = 'expert-message';
        answerDiv.innerHTML = `
            <div class="message-content">
                <div class="message-header">
                    <i class="fas fa-user-tie"></i> 
                    回合 ${turn.round} - 专家回答
                </div>
                <div class="message-text">${turn.answer}</div>
            </div>
        `;
        planContent.appendChild(answerDiv);
    });
    
    planContent.scrollTop = planContent.scrollHeight;
}

// 工具函数
function formatFactors(factors) {
    // ...existing formatting code...
}

function showError(message) {
    // 移除任何现有的错误提示
    const existing = document.querySelector('.error-toast');
    if (existing) {
        existing.remove();
    }
    
    const toast = document.createElement('div');
    toast.className = 'error-toast';
    toast.innerHTML = `
        <i class="fas fa-exclamation-circle"></i>
        <span>${message}</span>
    `;
    
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

function handleJsonResponse(response) {
    if (!response.ok) {
        throw new Error(response.statusText);
    }
    return response.json();
}

function formatList(items) {
    if (!Array.isArray(items)) return '';
    return '<ul>' + items.map(item => `<li>${item}</li>`).join('') + '</ul>';
}

// 移除重复的DOMContentLoaded监听器，保留一个完整的初始化函数
document.addEventListener('DOMContentLoaded', function() {
    initializeModules();
});

function initializeModules() {
    // 标签页切换
    document.querySelectorAll('.tab-btn').forEach(button => {
        button.addEventListener('click', () => handleTabChange(button));
    });

    // 各个表单的提交事件
    const forms = {
        'name-form': handleExpertSearch,
        'marketing-form': handleMarketingSubmit,
        'inventory-form': handleInventorySubmit
    };

    // 统一绑定表单事件
    Object.entries(forms).forEach(([id, handler]) => {
        const form = document.getElementById(id);
        if (form) {
            form.addEventListener('submit', handler);
        }
    });

    // 聊天功能初始化
    initializeChatFeatures();
}

function initializeChatFeatures() {
    const chatbotInput = document.getElementById('chatbot-input');
    const messageInput = document.getElementById('messageInput');

    if (chatbotInput) {
        chatbotInput.addEventListener('keypress', handleChatbotKeyPress);
    }

    if (messageInput) {
        messageInput.addEventListener('keypress', handleChatKeyPress);
    }
}

// 修复聊天相关函数
function handleChatbotKeyPress(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendChatbotMessage();
    }
}

function handleChatKeyPress(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
}

// 统一的API请求处理函数
async function apiRequest(url, method = 'POST', data = null) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000); // 30秒
    
    try {
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json'
            },
            signal: controller.signal
        };
        
        if (data) {
            options.body = JSON.stringify(data);
        }
        
        const response = await fetch(url, options);
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            throw new Error(`API错误: ${response.statusText}`);
        }
        
        return await response.json();
    } catch (error) {
        if (error.name === 'AbortError') {
            throw new Error('请求超时，请稍后重试');
        }
        console.error('请求失败:', error);
        showError('服务暂时不可用，请稍后再试');
        throw error;
    }
}

// 统一的错误处理
function handleError(error) {
    console.error('操作失败:', error);
    
    let message = '操作失败，请稍后重试';
    if (error.response) {
        // 服务器返回错误
        message = error.response.data.message || error.response.statusText;
    } else if (error.request) {
        // 网络错误
        message = '网络连接失败，请检查网络设置';
    }
    
    showError(message);
}

// 模块功能封装
const modules = {
    recruitment: {
        async search(category) {
            showLoading('正在匹配KOL...');
            try {
                const result = await apiRequest('/process', 'POST', { category });
                document.getElementById('result').innerHTML = this.formatResult(result);
                document.getElementById('result').style.display = 'block';
            } finally {
                hideLoading();
            }
        },
        formatResult(data) {
            return `<!-- 结果HTML模板 -->`;
        }
    },
    
    marketing: {
        async generate(data) {
            showLoading('生成营销方案...');
            try {
                const result = await apiRequest('/marketing/generate', 'POST', data);
                if (result.conversation) {
                    this.displayConversation(result.conversation);
                }
            } finally {
                hideLoading();
            }
        }
        // ...其他营销相关方法
    },
    
    inventory: {
        async analyze(data) {
            showLoading('分析库存策略...');
            try {
                const result = await apiRequest('/inventory/analyze', 'POST', data);
                this.updateResults(result);
            } finally {
                hideLoading();
            }
        }
        // ...其他库存相关方法
    },
    
    chat: {
        async sendMessage(message) {
            try {
                const result = await apiRequest('/chat', 'POST', { message });
                this.appendMessage('bot', result.response);
            } catch (error) {
                this.appendMessage('error', '消息发送失败');
            }
        }
        // ...其他聊天相关方法
    }
};
