export interface ComponentStatus {
  status: 'healthy' | 'unhealthy' | 'degraded';
  latency_ms?: number;
  message?: string;
}

export interface HealthCheckResponse {
  status: 'healthy' | 'unhealthy' | 'degraded';
  version: string;
  environment: string;
  timestamp: string;
  components: {
    database: ComponentStatus;
    redis: ComponentStatus;
    [key: string]: ComponentStatus;
  };
}
