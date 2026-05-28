# Script to wait for generation completion and then run concurrent evaluation
# Usage: .\run_evaluation_after_generation.ps1

$benchmarkFile = "output/1000q_diabetes_nota_benchmark_v2.jsonl"
$targetQuestions = 1000
$checkInterval = 60  # Check every 60 seconds
$maxWaitHours = 2     # Maximum wait time in hours

Write-Host "=" * 80
Write-Host "Waiting for benchmark generation to complete..."
Write-Host "Target file: $benchmarkFile"
Write-Host "Target questions: $targetQuestions"
Write-Host "=" * 80
Write-Host ""

$startTime = Get-Date
$maxWaitTime = $startTime.AddHours($maxWaitHours)

while ((Get-Date) -lt $maxWaitTime) {
    if (Test-Path $benchmarkFile) {
        $lines = (Get-Content $benchmarkFile | Measure-Object -Line).Lines
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Progress: $lines/$targetQuestions questions generated"
        
        if ($lines -ge $targetQuestions) {
            Write-Host ""
            Write-Host "=" * 80
            Write-Host "Generation complete! Starting concurrent evaluation..."
            Write-Host "=" * 80
            Write-Host ""
            
            # Run concurrent evaluation with 10 workers for faster processing
            python Concur_evaluate_benchmark_quality.py NOTA diabetes $benchmarkFile --workers 10 --checkpoint-freq 50
            
            Write-Host ""
            Write-Host "Evaluation complete!"
            exit 0
        }
    } else {
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Waiting for file to be created..."
    }
    
    Start-Sleep -Seconds $checkInterval
}

Write-Host ""
Write-Host "Timeout reached. Generation may still be in progress."
Write-Host "You can manually run the evaluation with:"
Write-Host "python Concur_evaluate_benchmark_quality.py NOTA diabetes $benchmarkFile --workers 10"
exit 1
