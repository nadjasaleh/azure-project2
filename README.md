# azure-project2

## Project Plan (3 Days)

### Day 1 – Foundation & Connectivity
1. Create Azure Resource Group, PostgreSQL database, Storage Account, Key Vault, and Virtual Machine  
2. Design database tables: `time_entries` and `consultant_balance`  
3. Create Flask API skeleton with a health endpoint  
4. Initialize GitHub repository and project structure  
5. Verify connectivity: Postman → API → PostgreSQL  

---

### Day 2 – Core Functionality
1. Implement `POST /time-entry` endpoint with input validation  
2. Store time entries in PostgreSQL and update consultant balance  
3. Create reporting script on the Virtual Machine (daily/weekly)  
4. Generate text-based report using SQL queries  
5. Upload report file to Azure Blob Storage  

---

### Day 3 – Polish, Demo & Presentation
1. Improve API responses and error handling  
2. Format report output for readability  
3. Finalize README and setup instructions  
4. Prepare demo flow and short presentation  
5. Run full end-to-end test before submission  
