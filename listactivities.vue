<template>
  <div>
    <v-toolbar flat>
      <v-toolbar-title>Activity Logs</v-toolbar-title>
      <v-spacer></v-spacer>
      <v-text-field
        v-model="search"
        append-icon="mdi-magnify"
        label="Search"
        single-line
        hide-details
      ></v-text-field>
      <v-btn color="primary" @click="detectface">Check</v-btn>
      <!-- ปุ่มนำไปยังหน้า Staff List -->
      <v-btn color="secondary" @click="goToStaffList"> Staff List</v-btn>
    </v-toolbar>

    <v-data-table
      :headers="headers"
      :items="filteredActivities"
    >
      <template v-slot:item.ts="{ item }">
        {{ formatDate(item.ts) }}
      </template>
      <template v-slot:item.Status="{ item }">
        {{ item.Status }} <!-- แสดงค่า status -->
      </template>

      <template v-slot:no-data>
        <v-btn color="primary" @click="initialize">Reset</v-btn>
        <p>No activities found. Please try again later.</p>
      </template>
    </v-data-table>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      search: '',
      headers: [
        { title: 'Staff ID', value: 'staffId', align: 'start' },
        { title: 'Timestamp', value: 'ts', align: 'start' },
        { title: 'Status', value: 'Status', align: 'start' },
        { title: 'Name', value: 'displayName', align: 'start' },
        { title: 'Department', value: 'dept', align: 'start' },
      ],
      activities: [],
    };
  },

  async created() {
    await this.initialize();
  },

  computed: {
    filteredActivities() {
      if (!this.search) {
        return this.activities;
      }
      return this.activities.filter(activity => {
        return (
          activity.staffId.toString().includes(this.search) ||
          activity.displayName.toLowerCase().includes(this.search.toLowerCase()) ||
          activity.dept.toLowerCase().includes(this.search.toLowerCase()) ||
          this.formatDate(activity.ts).includes(this.search) ||
          (activity.Status && activity.Status.toLowerCase().includes(this.search.toLowerCase()))
        );
      });
    }
  },

  methods: {
    async initialize() {
      try {
        const response = await axios.get('http://localhost:7000/listactivities', {
          headers: {
            'Content-Type': 'application/json',
          },
        });
        this.activities = response.data.rows || [];
      } catch (error) {
        console.error('Error fetching activities:', error);
        this.activities = [];
      }
    },

    async detectface() {
      try {
        const response = await axios.post('http://localhost:7000/run-detectface');
        console.log('Python script executed:', response.data);
        await this.initialize();
      } catch (error) {
        console.error('Error executing Python script:', error);
      }
    },

    goToStaffList() {
      this.$router.push('/liststaff'); // นำทางไปยังหน้า Staff List
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
