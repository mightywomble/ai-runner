# Zabbix to AI Runner Integration: A Complete Guide

This guide details how to configure a Zabbix instance to automatically trigger a diagnostic pipeline in an AI Runner application when a high CPU load is detected. The pipeline will run diagnostic tests, generate an AI summary, and post the results to a Discord channel.

This document assumes you have a working Zabbix server monitoring hosts with the Zabbix Agent.

## Part 1: AI Runner Configuration

Before touching Zabbix, we need to prepare the AI Runner application to receive the alert and act on it.

### Step 1: Create the Diagnostic Script

This script will run on the target machine when triggered.

1.  In the AI Runner UI, navigate to **Scripts** and click **Create Script**.
    
2.  **Name:**  `High CPU Triage`
    
3.  **Content:** Paste the following commands. This script captures essential performance metrics.
    
    ```
    echo "--- System Uptime and Load ---"
    uptime
    echo
    echo "--- Top 10 CPU-Consuming Processes ---"
    ps -eo pcpu,pid,user,args --sort=-pcpu | head -n 11
    echo
    echo "--- Top 10 Memory-Consuming Processes ---"
    ps -eo pmem,pid,user,args --sort=-pmem | head -n 11
    echo
    echo "--- Current Disk Usage ---"
    df -h
    
    ```
    
4.  Click **Save**.
    

### Step 2: Create a Discord Output

This tells AI Runner where to send the final report.

1.  Navigate to **Outputs** and click **Create Output**.
    
2.  **Name:**  `Discord Alerts Channel`
    
3.  **Type:**  `Discord`
    
4.  **Discord Webhook URL:** Paste the webhook URL from your Discord channel settings.
    
5.  Click **Save**.
    

### Step 3: Create the Pipeline

The pipeline ties the script and the output together.

1.  Navigate to **Pipelines** and click **Create Pipeline**.
    
2.  **Name:**  `Zabbix - High CPU Diagnostics`
    
3.  From the "Available Scripts" list, drag the **High CPU Triage** script to the "Selected Scripts" area.
    
4.  From the "Available Outputs" list, drag the **Discord Alerts Channel** output to the "Selected Outputs" area.
    
5.  Click **Save**.
    
6.  On the main "Pipelines" page, **note the ID of your new pipeline**. You will need this for the Zabbix configuration.
    

### Step 4: Get the API Key

Zabbix needs an API key to securely communicate with AI Runner.

1.  Navigate to **Admin** -> **Users**.
    
2.  Create a dedicated user for Zabbix (e.g., `zabbix_user`).
    
3.  From the user list, **copy the API Key** for the `zabbix_user`.
    

## Part 2: Zabbix Configuration

Now we will configure Zabbix to call the AI Runner pipeline.

### Step 1: Create the Webhook Media Type

This is the core component that knows how to talk to the AI Runner API.

1.  In the Zabbix UI, navigate to **Alerts → Media types**.
    
2.  Click **Create media type**.
    
3.  On the **Media type** tab, fill in the following:
    
    -   **Name:**  `AI Runner Webhook`
        
    -   **Type:**  `Webhook`
        
    -   **Parameters:** Define the data Zabbix will send. Add the following three rows:
        
        -   `pipeline_id`: `{EVENT.TAGS.pipeline_id}`
            
        -   `hostname`: `{HOST.HOST}`
            
        -   `trigger_name`: `{TRIGGER.NAME}`
            
4.  On the **Script** tab, paste the following JavaScript code. This version is confirmed to work with Zabbix's Duktape JavaScript engine.
    
    ```
    try {
        var params = JSON.parse(value);
    
        var AI_RUNNER_URL = "http(s)://<ai runner url>/api/zabbix/trigger"; // Your AI Runner URL
        var AI_RUNNER_API_KEY = "<ai runner API key for the zabbix_user>"; // Your API Key
    
        var request = new HttpRequest();
        request.addHeader('Content-Type: application/json');
        request.addHeader('X-API-Key: ' + AI_RUNNER_API_KEY);
    
        var body = JSON.stringify({
            pipeline_id: params.pipeline_id,
            hostname: params.hostname,
            trigger_name: params.trigger_name
        });
    
        var response = request.post(AI_RUNNER_URL, body);
    
        Zabbix.Log(4, 'AI Runner HTTP response: ' + request.getStatus() + ' ' + response);
    
        if (request.getStatus() < 200 || request.getStatus() >= 300) {
            throw 'Request failed with status code ' + request.getStatus() + '. Response: ' + response;
        }
    
        return JSON.stringify({
            tags: {
                ai_runner_status: 'triggered'
            }
        });
    }
    catch (error) {
        Zabbix.Log(4, 'AI Runner webhook failed: ' + error);
        throw 'AI Runner webhook failed: ' + error;
    }
    
    ```
    
5.  Click **Add** to save the media type.
    

### Step 2: Create a User and User Media

This links the webhook to a user profile that can receive alerts.

1.  Navigate to **Users → Users**.
    
2.  Create a new user (e.g., `ai-runner-user`) or use an existing one. Must be a super user and in the Zabbix administrators group
    
3.  Go to the **Media** tab for that user and click **Add**.
    
4.  In the pop-up, configure the media:
    
    -   **Type:** Select `AI Runner Webhook`.
        
    -   **Send to:** Enter `1` (this field is required but not used by our script).
        
    -   **Use if severity:** Check all severities you want this to apply to.
        
    -   **Enabled:** Ensure the status is toggled on.
        
5.  Click **Add**, then **Update** the user profile.
    

### Step 3: Create the High CPU Trigger

This is the condition that will start the entire alert process.

1.  Navigate to **Data collection → Hosts**.
    
2.  Find the host you want to monitor and click on its **Triggers**.
    
3.  Click **Create trigger**.
    
4.  On the **Trigger** tab:
    
    -   **Name:**  `High CPU utilization for 1 minute on {HOST.NAME}`
        
    -   **Severity:**  `High`
        
    -   **Expression:**  `max(/Your Host/system.cpu.util[,idle],1m)<=50`  _(This fires if CPU idle time is 50% or less for 1 minute)._
        
5.  Go to the **Tags** tab. This is a critical step.
    
    -   Click **Add** and create the following tag:
        
        -   **Name:**  `pipeline_id`
            
        -   **Value:** Enter the Pipeline ID you noted from AI Runner (e.g., `1`).
            
6.  Click **Add** to save the trigger.
    

### Step 4: Create the Alert Action

This is the final rule that connects the trigger event to the webhook.

1.  Navigate to **Alerts → Actions → Trigger actions**.
    
2.  Click **Create action**.
    
3.  On the **Action** tab:
    
    -   **Name:**  `Trigger AI Runner Pipeline`
        
    -   **Conditions:** Add a single condition: `Tag name`  `equals`  `pipeline_id`.
        
4.  Go to the **Operations** tab.
    
    -   Click the **Add** button in the "Operations" block.
        
    -   In the pop-up, configure the operation:
        
        -   **Send to users:** Select the `ai-runner-user`.
            
        -   **Send only to:** Select `AI Runner Webhook`.
            
        -   **Message:** Add some content (this is required by Zabbix).
            
            ```
            Trigger: {TRIGGER.NAME}
            Host: {HOST.NAME}
            Severity: {TRIGGER.SEVERITY}
            
            ```
            
    -   Click **Add** to save the operation.
        
5.  Click **Add** again to save the entire action.
    

## Part 3: The Workflow in Action

With everything configured, the following will happen when a host's CPU load is high:

1.  **Data Collection:** The Zabbix Agent on the host reports low CPU idle time to the Zabbix Server.
    
2.  **Problem Detection:** The "High CPU" trigger's expression becomes true, and a new problem is created in Zabbix.
    
3.  **Action Matching:** Zabbix sees that the problem has the `pipeline_id` tag and matches it with the `Trigger AI Runner Pipeline` action.
    
4.  **Webhook Execution:** The action's operation executes the `AI Runner Webhook` media type, sending the `pipeline_id`, `hostname`, and `trigger_name` to your AI Runner instance.
    
5.  **Pipeline Run:** AI Runner receives the API call, finds the correct pipeline, and runs the `High CPU Triage` script on the target host.
    
6.  **Notification:** Once the script finishes, the pipeline sends the complete output, including an AI-generated summary, to your configured Discord channel.
    

You have now successfully automated a diagnostic and reporting workflow, turning a simple Zabbix alert into actionable intelligence.
