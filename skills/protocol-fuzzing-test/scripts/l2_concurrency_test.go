package fuzzing_test

import (
	"context"
	"fmt"
	"math/rand"
	"runtime"
	"sync"
	"sync/atomic"
	"testing"
	"time"
)

// 假设这是你需要测试的 Modbus Client 接口
// type ModbusClient interface { ReadHoldingRegisters(...) }

func TestModbusClient_ConcurrentTIDIsolation(t *testing.T) {
	// 1. 开启 Block Profile 监控互斥锁阻塞情况
	runtime.SetBlockProfileRate(1)
	defer runtime.SetBlockProfileRate(0)

	// 初始化被测 Client（此处应指向配置了 Toxiproxy 延迟的模拟器）
	// client := NewModbusClient("127.0.0.1:5020")
	// defer client.Close()

	const (
		ConcurrencyLevel  = 50                      // 模拟 50 个 Goroutine 并发抢占
		RequestsPerGo     = 100                     // 每个协程发送 100 次请求
		MaxAllowedLatency = 200 * time.Millisecond  // 业务容忍的最大控制延迟
	)

	var wg sync.WaitGroup
	var crossTalkErrors int32
	var timeoutErrors int32

	startTime := time.Now()

	// 2. 启动高并发事务轰炸
	for i := 0; i < ConcurrencyLevel; i++ {
		wg.Add(1)
		go func(routineID int) {
			defer wg.Done()

			for j := 0; j < RequestsPerGo; j++ {
				// 构造特定的请求特征：使用 routineID 和序号作为期望的特征值
				expectedVal := uint16(routineID*1000 + j)
				regAddr := uint16(routineID % 100) // 分散读取地址

				reqStart := time.Now()

				// 发起调用 (需替换为实际驱动的调用方法)
				// resp, err := client.ReadHoldingRegisters(regAddr, 1)

				// 模拟耗时与结果获取 (Mock)
				time.Sleep(time.Duration(rand.Intn(10)) * time.Millisecond)
				var err error = nil
				var actualVal uint16 = expectedVal // 正常情况下应原样返回

				latency := time.Since(reqStart)

				if err != nil {
					atomic.AddInt32(&timeoutErrors, 1)
					continue
				}

				// 3. 核心断言一：延迟不超标 (排查锁粗放引起的排队)
				if latency > MaxAllowedLatency {
					t.Errorf("[Routine %d] Lock contention too high! Latency: %v", routineID, latency)
				}

				// 4. 核心断言二：防串话 (排查 TID 乱序分配)
				if actualVal != expectedVal {
					atomic.AddInt32(&crossTalkErrors, 1)
					t.Errorf("[FATAL] Cross-talk detected! Expected: %d, Got: %d", expectedVal, actualVal)
				}

				_ = regAddr
				_ = context.Background()
				_ = fmt.Sprintf("")
			}
		}(i)
	}

	wg.Wait()
	duration := time.Since(startTime)

	// 5. 汇总与判定
	t.Logf("Test completed in %v. Total Requests: %d", duration, ConcurrencyLevel*RequestsPerGo)

	if crossTalkErrors > 0 {
		t.Fatalf("Failed: Detected %d cross-talk events. Modbus TID mapping is corrupted under concurrency.", crossTalkErrors)
	}
	if timeoutErrors > 0 {
		t.Logf("Warning: %d requests timed out (Expected if Toxiproxy drop is active).", timeoutErrors)
	}

	// 6. （可选）在此处导出 pprof block 数据供后续火焰图分析
	// f, _ := os.Create("block.pprof")
	// pprof.Lookup("block").WriteTo(f, 0)
}
