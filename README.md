
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
   - **object table**: list of all objects in the database.

2. **Object Structure**:  
   - **ZTF ID**: Unique identifier from Lasair.  
   - **Object Properties**: Data and metadata from Lasair.  
   - **followup**: indicator if the object has been marked for followup.
   - **snoozed**: indicator if the object has been marked as snoozed.
   - **astronote**: indicator if the object has been marked as astronote.
   - **Comments**: User-added comments or notes for each object.  
   - **Link**: URL reference to the Lasair entry for further details.

---

## **Tutorial**
1. **Initialize the database**
   - `needle-track -i`
2. **Ingest data**
   - `needle-track ingest --slsn <path_to_data> --tde <path_to_data>`
3. **Search for objects**
   - `needle-track search --objectId/-o <object_id>`
   - `needle-track search --followup/-f`
   - `needle-track search --snoozed/-s`
   - `needle-track search --astronote/-a`
   - `needle-track search --list/-l`
4. **Update objects**
   - `needle-track update --objectId/-o <object_id> --followup/-f -c This is a comment`
   - `needle-track update --objectId/-o <object_id> --snoozed/-s -c This is a comment`
   - `needle-track update --objectId/-o <object_id> --astronote/-a -c This is a comment`
5. **Add comments**
   - `needle-track comment -o <object_id> This is a comment`