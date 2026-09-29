document.addEventListener("DOMContentLoaded", () => {
    // Scroll progress
    const progress = document.getElementById("progress");
    const updateProgress = () => {
        const max = document.documentElement.scrollHeight - window.innerHeight;
        progress.style.width = max > 0 ? `${(window.scrollY / max) * 100}%` : "0%";
    };
    window.addEventListener("scroll", updateProgress, {passive:true});
    updateProgress();

    // Reveal-on-scroll animations
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add("visible");
            }
        });
    }, {threshold: 0.14});

    document.querySelectorAll(".reveal").forEach(el => { el.classList.add("animate-hidden"); observer.observe(el); });

    // Counter animations
    const counters = document.querySelectorAll("[data-count]");
    const counterObserver = new IntersectionObserver((entries, obs) => {
        entries.forEach(entry => {
            if (!entry.isIntersecting) return;

            const el = entry.target;
            const target = Number(el.dataset.count);
            const isMoney = target > 1000;
            const isPercent = el.closest(".stat")?.querySelector("small")?.textContent === "RETURN";

            let start = 0;
            const duration = 1200;
            const startTime = performance.now();

            function tick(now) {
                const progressValue = Math.min((now - startTime) / duration, 1);
                const eased = 1 - Math.pow(1 - progressValue, 3);
                const value = target * eased;

                if (isMoney) {
                    el.textContent = "₹" + Math.round(value).toLocaleString("en-IN");
                } else if (isPercent) {
                    el.textContent = value.toFixed(1) + "%";
                } else {
                    el.textContent = Number.isInteger(target) ? Math.round(value) : value.toFixed(1);
                }

                if (progressValue < 1) requestAnimationFrame(tick);
            }

            requestAnimationFrame(tick);
            obs.unobserve(el);
        });
    }, {threshold:0.6});

    counters.forEach(el => counterObserver.observe(el));

    // Magnetic buttons
    document.querySelectorAll(".magnetic").forEach(button => {
        button.addEventListener("mousemove", e => {
            const rect = button.getBoundingClientRect();
            const x = (e.clientX - rect.left - rect.width / 2) * 0.18;
            const y = (e.clientY - rect.top - rect.height / 2) * 0.18;
            button.style.transform = `translate(${x}px, ${y}px)`;
        });

        button.addEventListener("mouseleave", () => {
            button.style.transform = "";
        });
    });

    // 3D dashboard parallax
    const frame = document.getElementById("dashboardFrame");
    window.addEventListener("scroll", () => {
        if (!frame) return;
        const rect = frame.getBoundingClientRect();
        const center = window.innerHeight / 2;
        const distance = (rect.top + rect.height / 2 - center) / window.innerHeight;
        const rotate = Math.max(-5, Math.min(5, distance * -7));
        const y = Math.max(-35, Math.min(35, distance * -35));
        frame.style.transform = `perspective(1400px) rotateX(${rotate}deg) translateY(${y}px)`;
    }, {passive:true});

    // Three.js background particles + market grid
    if (typeof THREE !== "undefined") {
        const canvas = document.getElementById("marketCanvas");
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(
            55,
            window.innerWidth / window.innerHeight,
            0.1,
            100
        );
        camera.position.z = 8;

        const renderer = new THREE.WebGLRenderer({
            canvas,
            alpha: true,
            antialias: true
        });
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.setSize(window.innerWidth, window.innerHeight);

        const particleCount = 900;
        const positions = new Float32Array(particleCount * 3);

        for (let i = 0; i < particleCount; i++) {
            positions[i * 3] = (Math.random() - 0.5) * 18;
            positions[i * 3 + 1] = (Math.random() - 0.5) * 11;
            positions[i * 3 + 2] = (Math.random() - 0.5) * 8;
        }

        const geometry = new THREE.BufferGeometry();
        geometry.setAttribute(
            "position",
            new THREE.BufferAttribute(positions, 3)
        );

        const material = new THREE.PointsMaterial({
            color: 0x49d66f,
            size: 0.025,
            transparent: true,
            opacity: 0.7
        });

        const particles = new THREE.Points(geometry, material);
        scene.add(particles);

        // Floating 3D cubes represent market data blocks.
        const cubeGroup = new THREE.Group();
        for (let i = 0; i < 22; i++) {
            const size = 0.08 + Math.random() * 0.18;
            const cube = new THREE.Mesh(
                new THREE.BoxGeometry(size, size, size),
                new THREE.MeshBasicMaterial({
                    color: 0x49d66f,
                    wireframe: true,
                    transparent: true,
                    opacity: 0.45
                })
            );
            cube.position.set(
                (Math.random() - 0.5) * 14,
                (Math.random() - 0.5) * 8,
                (Math.random() - 0.5) * 5
            );
            cubeGroup.add(cube);
        }
        scene.add(cubeGroup);

        let mouseX = 0;
        let mouseY = 0;

        window.addEventListener("mousemove", event => {
            mouseX = (event.clientX / window.innerWidth - 0.5) * 0.5;
            mouseY = (event.clientY / window.innerHeight - 0.5) * 0.5;
        });

        function animate() {
            requestAnimationFrame(animate);

            particles.rotation.y += 0.00035;
            particles.rotation.x += 0.00008;
            cubeGroup.rotation.y += 0.0007;
            cubeGroup.rotation.x += 0.00025;

            camera.position.x += (mouseX - camera.position.x) * 0.02;
            camera.position.y += (-mouseY - camera.position.y) * 0.02;
            camera.lookAt(scene.position);

            renderer.render(scene, camera);
        }

        animate();

        window.addEventListener("resize", () => {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        });
    }
});
