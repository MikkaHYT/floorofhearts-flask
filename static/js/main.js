document.addEventListener("DOMContentLoaded", () => {
    // Enable section animations if they exist
    const sections = document.querySelectorAll("section");
    sections.forEach((section) => {
        section.classList.add("enable-animation");
    });

    // Initialize carousel if it exists
    initCarousel();
});

// Carousel Functions
let slideIndex = 0;

function initCarousel() {
    const slides = document.querySelectorAll(".carousel img");
    if (slides.length === 0) return;

    // Show the first slide
    showSlide(slideIndex);

    // Auto advance slides every 5 seconds
    setInterval(() => {
        nextSlide();
    }, 5000);
}

function showSlide(n) {
    const slides = document.querySelectorAll(".carousel img");
    if (slides.length === 0) return;

    // Reset slideIndex if it's out of bounds
    if (n >= slides.length) slideIndex = 0;
    if (n < 0) slideIndex = slides.length - 1;

    // Hide all slides
    slides.forEach(slide => {
        slide.classList.remove("active");
    });

    // Show the current slide
    slides[slideIndex].classList.add("active");
}

function prevSlide() {
    showSlide(--slideIndex);
}

function nextSlide() {
    showSlide(++slideIndex);
}

// Handle thumbnail image clicks on product pages
function changeMainImage(src) {
    // This function is defined in the product.html template
    // but we declare it here to avoid errors in other pages
}

// Product filtering
document.addEventListener("DOMContentLoaded", () => {
    const filterForm = document.getElementById("filter-form");
    if (!filterForm) return;

    const products = document.querySelectorAll(".product");

    filterForm.addEventListener("change", () => {
        const selectedFilters = Array.from(
            filterForm.querySelectorAll("input[type='checkbox']:checked")
        ).map((checkbox) => checkbox.value);

        products.forEach((product) => {
            const productCategory = product.getAttribute("data-category");
            if (selectedFilters.length === 0 || selectedFilters.includes(productCategory)) {
                product.style.display = "block"; // Show product
            } else {
                product.style.display = "none"; // Hide product
            }
        });
    });
});

$(document).ready(function() {
    $('#productsTable').DataTable({
        responsive: true,
        dom: '<"top"lf>rt<"bottom"ip><"clear">',
        language: {
            search: "_INPUT_",
            searchPlaceholder: "Search...",
            lengthMenu: "Show _MENU_ entries"
        }
    });
});