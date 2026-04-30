Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
$ErrorActionPreference = 'Stop'

function Invoke-Step {
	param(
		[string]$Name,
		[scriptblock]$Action
	)

	Write-Host "Starting: $Name"
	try {
		& $Action
		if (-not $?) {
			Write-Host "FAILED: $Name - Last exit code: $LASTEXITCODE" -ForegroundColor Red
			exit 1
		}
	}
	catch {
		Write-Host "ERROR in step '$Name':" -ForegroundColor Red
		Write-Host "  Message   : $($_.Exception.Message)" -ForegroundColor Red
		Write-Host "  Type      : $($_.Exception.GetType().FullName)" -ForegroundColor Red
		Write-Host "  At        : $($_.InvocationInfo.ScriptName) line $($_.InvocationInfo.ScriptLineNumber)" -ForegroundColor Red
		Write-Host "  Statement : $($_.InvocationInfo.Line.Trim())" -ForegroundColor Red
		exit 1
	}
}

function Wait-HttpReady {
	param(
		[string]$Name,
		[string]$Url,
		[int]$TimeoutSeconds = 180,
		[int]$PollSeconds = 2
	)

	$deadline = (Get-Date).AddSeconds($TimeoutSeconds)
	while ((Get-Date) -lt $deadline) {
		try {
			$response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5
			if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 300) {
				Write-Host "Ready: $Name ($Url)"
				return
			}
		}
		catch {
			# Keep polling until timeout because services may be in warm-up.
		}

		Start-Sleep -Seconds $PollSeconds
	}

	throw "Timed out waiting for $Name at $Url after $TimeoutSeconds seconds."
}

# Run each step synchronously and stop on first failure.
Invoke-Step -Name 'stop-native2' -Action {
	& C:\code\openTel_2\central\stop-native2.ps1
}

Invoke-Step -Name 'stop-agent' -Action {
	& C:\code\openTel_2\agent\stop-agent.ps1
}

Invoke-Step -Name 'cleanup-trace-logs' -Action {
	Remove-Item -Recurse -Force C:\code\openTel_2\central\bin\tempo-metrics-wal* -ErrorAction SilentlyContinue
	Remove-Item -Recurse -Force C:\code\openTel_2\central\bin\tempo-blocks* -ErrorAction SilentlyContinue
	Remove-Item -Recurse -Force C:\code\openTel_2\central\bin\tempo-index* -ErrorAction SilentlyContinue
	Remove-Item -Recurse -Force C:\code\openTel_2\central\bin\tempo-wal* -ErrorAction SilentlyContinue
	Remove-Item -Recurse -Force C:\code\openTel_2\central\bin\tempo-data* -ErrorAction SilentlyContinue
	Remove-Item -Recurse -Force C:\code\openTel_2\central\bin\metrics* -ErrorAction SilentlyContinue
}

Invoke-Step -Name 'start-native2' -Action {
	& C:\code\openTel_2\central\start-native2.ps1
}

Invoke-Step -Name 'wait-observability-ready' -Action {
	Wait-HttpReady -Name 'OpenTelemetry Collector' -Url 'http://localhost:13133' -TimeoutSeconds 120
	Wait-HttpReady -Name 'Loki' -Url 'http://localhost:3100/ready' -TimeoutSeconds 180
	Wait-HttpReady -Name 'Tempo' -Url 'http://localhost:3200/ready' -TimeoutSeconds 180
}

Invoke-Step -Name 'start-agent' -Action {
	& C:\code\openTel_2\agent\start-agent.ps1
}

Invoke-Step -Name 'start_all_servers.py' -Action {
	Push-Location C:\code\openTel_2_simulation
	try {
		& python .\start_all_servers.py
	} finally {
		Pop-Location
	}
	if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

Invoke-Step -Name 'run_ccsf_chain.py' -Action {
	& python C:\code\openTel_2_simulation\run_ccsf_chain.py --runs 1
	if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

Invoke-Step -Name 'run_abpt_chains.py' -Action {
	& python C:\code\openTel_2_simulation\run_abpt_chains.py --chain test_scenario_1,test_scenario_2,test_scenario_3,test_scenario_4,test_scenario_6,test_scenario_7,test_scenario_8,test_scenario_9,test_scenario_10 --runs 15
	if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

#Invoke-Step -Name 'run_abpt_chain_test_scenario_5.py' -Action {
#	& python C:\code\openTel_2_simulation\run_abpt_chains.py --chain test_scenario_5 --runs 5
#	if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
#}

Invoke-Step -Name 'trace_to_bpmn2.py' -Action {
	& python C:\code\openTel_2\tests\trace_to_bpmn2.py --limit 30 --last-hours 1 --traceql '{ span."Business_Flow_ID" != nil }'
	if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
Invoke-Step -Name 'xml2json.py' -Action {
	& python C:\code\openTel_2\tests\xml2json.py
	if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}