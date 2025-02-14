
# **NEEDLE-TRACK**  
**Transient Recognition, Annotation, and Classification Kit**

## **System Overview**  
NEEDLE-TRACK is a local system (with future migration potential to cloud or other machines) for managing transient data from Lasair (ZTF). It provides structured data storage, update tracking, search capabilities, and a publicly available package for easy deployment.

## **Core Components**  
1. **Local System Management**  
   - Designed to run locally, with future migration capability to cloud or other machines.  
   - Configuration options allow users to set up the system on various environments.

2. **Database for Data Storage**  
   - Stores transient objects with changeable tags and associated comments for further annotation.  
   - Maintains an **Update List** to track objects whose data has changed or that have new incoming updates.  
   - Supports updates and tracking of object status changes.

3. **Terminal Interface**  
   - Users interact with the system through a command-line interface (CLI).  
   - Provides commands for ingestion, searching, commenting, and annotation.

4. **Search Function**  
   - Query objects by unique ZTF ID.  
   - Filter objects based on tags.  
   - Search based on annotation status (astronote presence).

5. **Public Package Distribution**  
   - The package, named `needle_track`, is hosted on GitHub for public access.  
   - Includes installation instructions, dependencies, and usage guidelines.

---

## **Data Ingestion**  
1. **Source**: Data exported from Lasair broker (ZTF).  
2. **Format**: JSON.  
3. **Update Mechanism**:  
   - Runs a script to fetch the latest data (default: past week, customizable).  
   - Checks for overlapping entries:  
     - **Overlap Check**: Compares incoming data with existing records.  
       - If overlaps are detected, the system updates the existing record and logs it into the **Update List**.  
       - New records are added directly to the database.  
       - Objects that are not interested are moved to the **Removed List**.  
   - Generates a report summarizing all updates and changes.


## **Data Storage**  
1. **SQL Database Structure**:  
   - **Follow-up List**: Objects marked for continued observation.  
   - **New List**: Recently ingested objects.  
   - **Removed List**: Objects no longer relevant.  
   - **Astronote List**: Objects with associated annotations.  
   - **Update List**: Objects that have been updated with new data upon ingestion.

2. **Object Structure**:  
   - **ZTF ID**: Unique identifier from Lasair.  
   - **Object Properties**: Data and metadata from Lasair.  
   - **Changeable Tags**: Categories or status markers that can be updated.  
   - **Comments**: User-added comments or notes for each object.  
   - **Astronote Status**: Indicator if the object has an annotation.  
   - **Link**: URL reference to the Lasair entry for further details.

---

## **Search Functionality**  
1. **Search by ZTF ID**: Retrieve detailed information for a specific object.  
2. **Search by Tag**: Filter objects based on assigned or updated categories.  
3. **Search by Astronote Status**: Identify objects with associated annotations.  
4. **Review Update List**: Optionally, users can search or filter for objects in the update list to quickly identify recent changes.

