<template>
  <div>
    <v-toolbar flat>
      <v-toolbar-title>Staff List</v-toolbar-title>
      <v-spacer></v-spacer>

      <v-text-field
        v-model="search"
        append-icon="mdi-magnify"
        label="Search"
        single-line
        hide-details
      ></v-text-field>

      <v-btn color="primary" @click="openRegisterDialog">Register</v-btn>
      <v-btn color="secondary" @click="goToStaffList"> Activity Logs </v-btn>
    </v-toolbar>

    <v-data-table
      :headers="headers"
      :items="filteredStaffs"
    >
      <template v-slot:item.ts="{ item }">
        {{ formatDate(item.ts) }}
      </template>

      <template v-slot:item.actions="{ item }">
        <v-btn color="blue" @click="openUpdateDialog(item)">Update</v-btn>
        <v-btn color="red" @click="deleteStaff(item.id)">Delete</v-btn>
      </template>

      <template v-slot:no-data>
        <v-btn color="primary" @click="initialize">Reset</v-btn>
        <p>No staff data found. Please try again later.</p>
      </template>
    </v-data-table>

    <!-- Dialog สำหรับ Register -->
    <v-dialog v-model="registerDialog" max-width="500px">
      <v-card>
        <v-card-title>
          <span class="headline">Register</span>
        </v-card-title>

        <v-card-text>
          <v-form ref="registerForm">
            <v-text-field v-model="registerForm.displayName" label="Name" required></v-text-field>
            <v-text-field v-model="registerForm.dept" label="Department" required></v-text-field>
          </v-form>
        </v-card-text>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" @click="submitRegisterForm">Submit</v-btn>
          <v-btn @click="registerDialog = false">Cancel</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Dialog สำหรับ Update -->
    <v-dialog v-model="updateDialog" max-width="500px">
      <v-card>
        <v-card-title>
          <span class="headline">Update Staff</span>
        </v-card-title>

        <v-card-text>
          <v-form ref="updateForm">
            <v-text-field v-model="updateForm.displayName" label="Name" required></v-text-field>
            <v-text-field v-model="updateForm.dept" label="Department" required></v-text-field>
          </v-form>
        </v-card-text>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" @click="submitUpdateForm">Update</v-btn>
          <v-btn @click="updateDialog = false">Cancel</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      search: '',
      headers: [
        { title: 'ID', value: 'id', align: 'start' },
        { title: 'Name', value: 'displayName', align: 'start' },
        { title: 'Department', value: 'dept', align: 'start' },
        { title: '', value: 'actions', align: 'end' },
      ],
      staffs: [],
      registerDialog: false,
      updateDialog: false,
      registerForm: {
        displayName: '',
        dept: '',
      },
      updateForm: {
        id: '',
        displayName: '',
        dept: '',
      },
    };
  },

  async created() {
    await this.initialize();
  },

  computed: {
    filteredStaffs() {
      if (!this.search) {
        return this.staffs;
      }
      return this.staffs.filter(staff => {
        return (
          staff.id.toString().includes(this.search) ||
          staff.displayName.toLowerCase().includes(this.search.toLowerCase()) ||
          staff.dept.toLowerCase().includes(this.search.toLowerCase())
        );
      });
    }
  },

  methods: {
    goToStaffList() {
      this.$router.push('/listactivities'); // นำทางไปยังหน้า Staff List
    },

    async initialize() {
      try {
        const response = await axios.get('http://localhost:7000/staffs', {
          headers: {
            'Content-Type': 'application/json',
          },
        });
        this.staffs = response.data || [];
      } catch (error) {
        console.error('Error fetching staff data:', error);
        this.staffs = [];
      }
    },

    openRegisterDialog() {
      this.registerForm = {
        displayName: '',
        dept: '',
      };
      this.registerDialog = true;
    },

    async submitRegisterForm() {
      if (!this.registerForm.displayName || !this.registerForm.dept) {
        alert('Both Name and Department are required!');
        return;
      }

      try {
        const response = await axios.post('http://localhost:7000/register', this.registerForm);
        console.log('Registration successful:', response.data);
        this.registerDialog = false;
        await this.initialize(); // โหลดข้อมูลใหม่
      } catch (error) {
        console.error('Error during registration:', error.response ? error.response.data : error.message);
      }
    },

    openUpdateDialog(staff) {
      this.updateForm = { ...staff }; // กำหนดข้อมูลพนักงานที่ต้องการอัปเดต
      this.updateDialog = true;
    },

    async submitUpdateForm() {
      if (!this.updateForm.displayName || !this.updateForm.dept) {
        alert('Both Name and Department are required!');
        return;
      }

      try {
        const response = await axios.put(`http://localhost:7000/update-staff/${this.updateForm.id}`, this.updateForm);
        console.log('Update successful:', response.data);
        this.updateDialog = false;
        await this.initialize(); // โหลดข้อมูลใหม่
      } catch (error) {
        console.error('Error during update:', error.response ? error.response.data : error.message);
      }
    },

    async deleteStaff(id) {
      if (confirm('Are you sure you want to delete this staff?')) {
        try {
          const response = await axios.delete(`http://localhost:7000/delete-staff/${id}`);
          console.log('Deletion successful:', response.data);
          await this.initialize(); // โหลดข้อมูลใหม่
        } catch (error) {
          console.error('Error during deletion:', error.response ? error.response.data : error.message);
        }
      }
    },

    formatDate(timestamp) {
      const options = {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false,
      };
      return new Date(timestamp).toLocaleString(undefined, options);
    }
  }
}

</script>
