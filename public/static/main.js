// --- Mobile Menu Toggle ---
function toggleMobileMenu() {
    const menu = document.getElementById('mobile-menu');
    menu.classList.toggle('hidden');
}

// --- Sidebar Logic ---
function openSidebar(card) {
    const mode = card.getAttribute('data-mode');
    const sidebar = document.getElementById('project-sidebar');
    const standardContent = document.getElementById('sb-standard-content');
    const generatorContent = document.getElementById('sb-generator-content');
    const ctaContainer = document.getElementById('sb-cta-container');

    if (mode === 'generator') {
        standardContent.classList.add('hidden');
        ctaContainer.classList.add('hidden');
        generatorContent.classList.remove('hidden');
    } else {
        const title = card.getAttribute('data-title');
        const desc = card.getAttribute('data-desc');
        const type = card.getAttribute('data-type');
        const ctaLink = card.getAttribute('data-cta');
        const ctaText = card.getAttribute('data-cta-text');
        const iconClass = card.getAttribute('data-icon');
        const imageUrl = card.getAttribute('data-image');
        const stack = card.getAttribute('data-stack');

        document.getElementById('sb-title').innerText = title;
        document.getElementById('sb-desc').innerText = desc;
        document.getElementById('sb-type').innerText = type;
        document.getElementById('sb-cta').href = ctaLink;
        document.getElementById('sb-cta').innerText = ctaText;
        document.getElementById('sb-stack').innerText = stack || 'AI + NoCode';

        const iconElement = document.getElementById('sb-icon');
        iconElement.className = iconClass.includes('fa-regular') ? iconClass : `fa-solid ${iconClass}`;

        // Handle screenshot area - show image if available, else show placeholder
        const screenshotArea = document.querySelector('[data-screenshot]');
        if (imageUrl) {
            screenshotArea.innerHTML = `<img src="${imageUrl}" alt="${title}" class="w-full h-full object-cover">`;
        } else {
            screenshotArea.innerHTML = `<div class="text-center p-6"><i class="fa-regular fa-image text-4xl text-neutral-400 mb-2 group-hover:scale-110 transition-transform"></i><p class="text-neutral-500 text-sm">App Screenshot</p></div>`;
        }

        generatorContent.classList.add('hidden');
        standardContent.classList.remove('hidden');
        ctaContainer.classList.remove('hidden');
    }

    document.body.classList.add('sidebar-open');
    const overlay = document.getElementById('sidebar-overlay');
    overlay.classList.remove('hidden');
    setTimeout(() => {
        overlay.classList.remove('opacity-0');
        sidebar.classList.remove('translate-x-full');
    }, 10);
}

function closeSidebar() {
    const overlay = document.getElementById('sidebar-overlay');
    const sidebar = document.getElementById('project-sidebar');
    overlay.classList.add('opacity-0');
    sidebar.classList.add('translate-x-full');
    document.body.classList.remove('sidebar-open');
    setTimeout(() => {
        overlay.classList.add('hidden');
    }, 300);
}

async function generatePrompt() {
    const input = document.getElementById('prompt-input').value;
    if (!input) return;

    const outputContainer = document.getElementById('generator-output-container');
    const loading = document.getElementById('generator-loading');
    const outputText = document.getElementById('prompt-output');
    
    outputContainer.classList.remove('hidden');
    loading.classList.remove('hidden');
    outputText.value = "";

    try {
        const response = await fetch('/api/generate-prompt', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ input: input })
        });

        const data = await response.json();
        
        if (data.error) {
            outputText.value = "Error generating prompt: " + data.error;
        } else {
            outputText.value = data.text || "Error generating prompt. Please try again.";
        }
    } catch (error) {
        console.error("API Error:", error);
        outputText.value = "Sorry, I hit a snag connecting to the AI. Check console for details.";
    } finally {
        loading.classList.add('hidden');
    }
}

function copyPrompt() {
    const copyText = document.getElementById("prompt-output");
    copyText.select();
    document.execCommand("copy");
}

async function runVibeCheck() {
    const toast = document.getElementById('vibe-toast');
    const toastText = document.getElementById('vibe-toast-text');
    
    toastText.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Checking the vibes...';
    toast.classList.remove('opacity-0', 'translate-y-[-20px]');
    toast.style.pointerEvents = 'auto';

    try {
        const response = await fetch('/api/vibe-check', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const data = await response.json();
        
        if (data.error) {
            toastText.innerText = "Vibes are off: " + data.error;
        } else {
            toastText.innerText = `"${data.text || 'Ship it. Fix it later.'}"`;
        }

        setTimeout(() => {
            toast.classList.add('opacity-0', 'translate-y-[-20px]');
            toast.style.pointerEvents = 'none';
        }, 5000);

    } catch (error) {
        console.error("Vibe Check Error:", error);
        toastText.innerText = "Vibes are off (API Error). Try again.";
        setTimeout(() => {
            toast.classList.add('opacity-0', 'translate-y-[-20px]');
            toast.style.pointerEvents = 'none';
        }, 5000);
    }
}
