using Microsoft.Spark.Sql;
using System;

class Program
{
    static void Main(string[] args)
    {
        // Initialize Spark session
        SparkSession spark = SparkSession.Builder()
            .AppName("UpdateDeltaTableExample")
            .GetOrCreate();

        // Define the Delta table path
        string deltaTablePath = "/mnt/delta_table";

        // Read the existing Delta table into a DataFrame
        DataFrame existingTable = spark.Read()
            .Format("delta")
            .Load(deltaTablePath);

        // Sample data for updates
        var updates = new[]
        {
            new { Id = 1, Name = "Alice Updated", ModifiedDate = DateTime.UtcNow },
            new { Id = 2, Name = "Bob Updated", ModifiedDate = DateTime.UtcNow }
        };

        // Create a DataFrame from the update data
        DataFrame updateDF = spark.CreateDataFrame(updates);

        // Perform the update using a join and a condition
        DataFrame updatedTable = existingTable
            .Alias("existing")
            .Join(updateDF.Alias("updates"), 
                existingTable["Id"] == updateDF["Id"], 
                "left_outer")
            .SelectExpr(
                "coalesce(updates.Name, existing.Name) as Name",
                "existing.Id",
                "coalesce(updates.ModifiedDate, existing.ModifiedDate) as ModifiedDate"
            );

        // Overwrite the existing Delta table with updated data
        updatedTable.Write()
            .Format("delta")
            .Mode("overwrite")
            .Save(deltaTablePath);

        Console.WriteLine("Delta table updated successfully!");

        // Stop the Spark session
        spark.Stop();
    }
}
