/**
 * BLOOD BANK MANAGEMENT SYSTEM
 * Vanilla JavaScript helper utilities
 */

document.addEventListener("DOMContentLoaded", () => {
  // 1. Mobile Sidebar Toggle
  const sidebar = document.getElementById("sidebar");
  const menuToggle = document.getElementById("menuToggle");
  if (menuToggle && sidebar) {
    menuToggle.addEventListener("click", () => {
      sidebar.classList.toggle("open");
    });
  }

  // Close sidebar when clicking outside on mobile
  document.addEventListener("click", (e) => {
    if (window.innerWidth <= 768 && sidebar && sidebar.classList.contains("open")) {
      if (!sidebar.contains(e.target) && !menuToggle.contains(e.target)) {
        sidebar.classList.remove("open");
      }
    }
  });

  // 2. Real-time Clock in Topbar
  const liveClockEl = document.getElementById("liveClock");
  if (liveClockEl) {
    const updateTime = () => {
      const now = new Date();
      liveClockEl.textContent = now.toLocaleDateString("en-US", {
        weekday: "short",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit"
      });
    };
    updateTime();
    setInterval(updateTime, 1000);
  }

  // 3. Modal Opening and Closing
  window.openModal = function (modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.add("open");
      document.body.style.overflow = "hidden";
    }
  };

  window.closeModal = function (modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.remove("open");
      document.body.style.overflow = "";
    }
  };

  // Close modal on backdrop click
  document.querySelectorAll(".modal-backdrop").forEach((backdrop) => {
    backdrop.addEventListener("click", (e) => {
      if (e.target === backdrop) {
        backdrop.classList.remove("open");
        document.body.style.overflow = "";
      }
    });
  });

  // 4. Flash Alert Dismiss
  document.querySelectorAll(".alert-close").forEach((btn) => {
    btn.addEventListener("click", () => {
      const alert = btn.closest(".alert");
      if (alert) {
        alert.style.opacity = "0";
        setTimeout(() => alert.remove(), 200);
      }
    });
  });

  // 5. Fill Demo Credentials
  window.fillLogin = function (username, password) {
    const userField = document.getElementById("username");
    const passField = document.getElementById("password");
    if (userField && passField) {
      userField.value = username;
      passField.value = password;
      userField.focus();
    }
  };

  // 6. Populate Edit Donor Modal
  window.populateEditDonor = function (donor) {
    document.getElementById("edit_donor_id").value = donor.donor_id;
    document.getElementById("edit_full_name").value = donor.full_name;
    document.getElementById("edit_age").value = donor.age;
    document.getElementById("edit_gender").value = donor.gender;
    document.getElementById("edit_blood_group").value = donor.blood_group;
    document.getElementById("edit_phone").value = donor.phone;
    document.getElementById("edit_email").value = donor.email || "";
    document.getElementById("edit_address").value = donor.address || "";
    
    const form = document.getElementById("editDonorForm");
    form.action = `/donors/edit/${donor.donor_id}`;
    openModal("editDonorModal");
  };

  // 7. Auto-detect blood group in donation modal when selecting donor
  const donorSelect = document.getElementById("donation_donor_select");
  const bloodGroupDisplay = document.getElementById("donation_blood_group_display");
  if (donorSelect && bloodGroupDisplay) {
    donorSelect.addEventListener("change", function () {
      const selectedOption = this.options[this.selectedIndex];
      const bg = selectedOption.getAttribute("data-blood-group");
      if (bg) {
        bloodGroupDisplay.textContent = bg;
        bloodGroupDisplay.parentElement.style.display = "block";
      } else {
        bloodGroupDisplay.parentElement.style.display = "none";
      }
    });
  }

  // Initialize Lucide icons if available
  if (window.lucide) {
    window.lucide.createIcons();
  }
});
