"use client"

import { useState, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { 
  Brain, Zap, TrendingUp, Target, Settings, 
  CheckCircle2, AlertCircle, Sparkles, ChevronRight,
  BarChart3, Activity, Loader2, Download, Star
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { Slider } from "@/components/ui/slider"
import { DashboardHeader } from "@/components/dashboard-header"
import { useToast } from "@/hooks/use-toast"
import {
  trainXGBoost,
  trainNeuralNetwork,
  compareModels,
  getFeatureSuggestions,
  getSupportedAlgorithms,
  getDatasetsList
} from "@/lib/api"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"

export default function MLTrainingPage() {
  const { toast } = useToast()
  
  // State
  const [step, setStep] = useState(1)
  const [datasets, setDatasets] = useState<any[]>([])
  const [selectedDataset, setSelectedDataset] = useState<any>(null)
  const [algorithm, setAlgorithm] = useState("xgboost")
  const [target, setTarget] = useState("")
  const [features, setFeatures] = useState<string[]>([])
  const [training, setTraining] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [suggestions, setSuggestions] = useState<any>(null)
  
  // XGBoost parameters
  const [nEstimators, setNEstimators] = useState(100)
  const [maxDepth, setMaxDepth] = useState(6)
  const [learningRate, setLearningRate] = useState(0.1)
  const [tuneHyperparameters, setTuneHyperparameters] = useState(false)
  
  // Neural Network parameters
  const [hiddenLayers, setHiddenLayers] = useState("64,32")
  const [dropoutRate, setDropoutRate] = useState(0.2)
  const [epochs, setEpochs] = useState(50)
  const [batchSize, setBatchSize] = useState(32)
  
  // General parameters
  const [testSize, setTestSize] = useState(0.2)
  const [saveModel, setSaveModel] = useState(true)

  useEffect(() => {
    loadDatasets()
  }, [])

  const loadDatasets = async () => {
    try {
      const response = await getDatasetsList()
      setDatasets(response.datasets || [])
    } catch (error: any) {
      toast({
        title: "Failed to load datasets",
        description: error.message,
        variant: "destructive"
      })
    }
  }

  const handleDatasetSelect = async (datasetId: string) => {
    const dataset = datasets.find(d => d.id === parseInt(datasetId))
    setSelectedDataset(dataset)
    
    // Reset selections
    setTarget("")
    setFeatures([])
    setSuggestions(null)
  }

  const handleTargetSelect = async (targetCol: string) => {
    setTarget(targetCol)
    
    // Get feature suggestions
    if (selectedDataset) {
      try {
        const response = await getFeatureSuggestions(selectedDataset.id, targetCol)
        setSuggestions(response.suggestions)
      } catch (error) {
        console.error("Failed to get feature suggestions:", error)
      }
    }
  }

  const handleFeatureToggle = (feature: string) => {
    if (features.includes(feature)) {
      setFeatures(features.filter(f => f !== feature))
    } else {
      setFeatures([...features, feature])
    }
  }

  const handleTrain = async () => {
    if (!selectedDataset || !target) {
      toast({
        title: "Missing information",
        description: "Please select dataset and target variable",
        variant: "destructive"
      })
      return
    }

    setTraining(true)
    setResult(null)

    try {
      let response

      if (algorithm === "xgboost") {
        response = await trainXGBoost({
          dataset_id: selectedDataset.id,
          target,
          features: features.length > 0 ? features : undefined,
          test_size: testSize,
          n_estimators: nEstimators,
          max_depth: maxDepth,
          learning_rate: learningRate,
          tune_hyperparameters: tuneHyperparameters,
          save_model: saveModel
        })
      } else {
        const layers = hiddenLayers.split(',').map(l => parseInt(l.trim())).filter(l => !isNaN(l))
        response = await trainNeuralNetwork({
          dataset_id: selectedDataset.id,
          target,
          features: features.length > 0 ? features : undefined,
          test_size: testSize,
          hidden_layers: layers,
          dropout_rate: dropoutRate,
          epochs,
          batch_size: batchSize,
          save_model: saveModel
        })
      }

      setResult(response.result)
      setStep(4)

      toast({
        title: "✅ Model Trained Successfully!",
        description: `${algorithm === 'xgboost' ? 'XGBoost' : 'Neural Network'} model trained in ${response.result.execution_time_ms}ms`
      })

    } catch (error: any) {
      toast({
        title: "Training Failed",
        description: error.message,
        variant: "destructive"
      })
    } finally {
      setTraining(false)
    }
  }

  const getAvailableColumns = () => {
    if (!selectedDataset?.columns) return []
    try {
      return JSON.parse(selectedDataset.columns)
    } catch {
      return []
    }
  }

  const getMetricColor = (value: number, metric: string) => {
    if (metric.includes('accuracy') || metric.includes('r2')) {
      return value > 0.8 ? 'text-green-600' : value > 0.6 ? 'text-yellow-600' : 'text-red-600'
    }
    return 'text-blue-600'
  }

  return (
    <div className="space-y-6">
      <DashboardHeader
        title="ML Model Training"
        description="Train advanced machine learning models with XGBoost and Neural Networks"
      />

      {/* Progress Steps */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            {[1, 2, 3, 4].map((s) => (
              <div key={s} className="flex items-center">
                <div className={`flex items-center justify-center w-10 h-10 rounded-full border-2 ${
                  step >= s ? 'border-primary bg-primary text-primary-foreground' : 'border-muted'
                }`}>
                  {step > s ? <CheckCircle2 className="h-5 w-5" /> : s}
                </div>
                {s < 4 && (
                  <div className={`w-24 h-0.5 mx-2 ${
                    step > s ? 'bg-primary' : 'bg-muted'
                  }`} />
                )}
              </div>
            ))}
          </div>
          <div className="flex justify-between mt-2 text-xs text-muted-foreground">
            <span>Dataset</span>
            <span>Algorithm</span>
            <span>Parameters</span>
            <span>Results</span>
          </div>
        </CardContent>
      </Card>

      {/* Step 1: Select Dataset */}
      {step === 1 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Step 1: Select Dataset
              </CardTitle>
              <CardDescription>
                Choose the dataset you want to train a model on
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label>Dataset</Label>
                <Select onValueChange={handleDatasetSelect}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select a dataset" />
                  </SelectTrigger>
                  <SelectContent>
                    {datasets.map((dataset) => (
                      <SelectItem key={dataset.id} value={dataset.id.toString()}>
                        {dataset.name} ({dataset.num_rows} rows, {dataset.num_columns} columns)
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {selectedDataset && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="p-4 border rounded-lg">
                      <p className="text-sm text-muted-foreground">Rows</p>
                      <p className="text-2xl font-bold">{selectedDataset.num_rows?.toLocaleString()}</p>
                    </div>
                    <div className="p-4 border rounded-lg">
                      <p className="text-sm text-muted-foreground">Columns</p>
                      <p className="text-2xl font-bold">{selectedDataset.num_columns}</p>
                    </div>
                    <div className="p-4 border rounded-lg">
                      <p className="text-sm text-muted-foreground">Size</p>
                      <p className="text-2xl font-bold">
                        {(selectedDataset.file_size / 1024 / 1024).toFixed(2)} MB
                      </p>
                    </div>
                    <div className="p-4 border rounded-lg">
                      <p className="text-sm text-muted-foreground">Type</p>
                      <p className="text-2xl font-bold">{selectedDataset.file_type}</p>
                    </div>
                  </div>

                  <div>
                    <Label>Target Variable (What to predict)</Label>
                    <Select onValueChange={handleTargetSelect} value={target}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select target variable" />
                      </SelectTrigger>
                      <SelectContent>
                        {getAvailableColumns().map((col: string) => (
                          <SelectItem key={col} value={col}>
                            {col}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {target && (
                    <div>
                      <Label>Features (Leave empty to auto-select all except target)</Label>
                      <div className="flex flex-wrap gap-2 mt-2">
                        {getAvailableColumns()
                          .filter((col: string) => col !== target)
                          .map((col: string) => (
                            <Badge
                              key={col}
                              variant={features.includes(col) ? "default" : "outline"}
                              className="cursor-pointer"
                              onClick={() => handleFeatureToggle(col)}
                            >
                              {col}
                            </Badge>
                          ))}
                      </div>
                    </div>
                  )}

                  <Button 
                    onClick={() => setStep(2)} 
                    className="w-full"
                    disabled={!target}
                  >
                    Continue to Algorithm Selection
                    <ChevronRight className="ml-2 h-4 w-4" />
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Step 2: Select Algorithm */}
      {step === 2 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Brain className="h-5 w-5" />
                Step 2: Select Algorithm
              </CardTitle>
              <CardDescription>
                Choose the machine learning algorithm
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Card 
                  className={`cursor-pointer transition-all ${
                    algorithm === 'xgboost' ? 'border-primary ring-2 ring-primary' : ''
                  }`}
                  onClick={() => setAlgorithm('xgboost')}
                >
                  <CardContent className="pt-6">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="p-2 bg-blue-100 rounded-lg">
                        <Zap className="h-6 w-6 text-blue-600" />
                      </div>
                      <div>
                        <h3 className="font-semibold">XGBoost</h3>
                        <p className="text-sm text-muted-foreground">Gradient Boosting</p>
                      </div>
                    </div>
                    <ul className="text-sm space-y-1 text-muted-foreground">
                      <li>✓ Excellent for tabular data</li>
                      <li>✓ Fast training speed</li>
                      <li>✓ High accuracy</li>
                      <li>✓ Feature importance</li>
                    </ul>
                  </CardContent>
                </Card>

                <Card 
                  className={`cursor-pointer transition-all ${
                    algorithm === 'neural_network' ? 'border-primary ring-2 ring-primary' : ''
                  }`}
                  onClick={() => setAlgorithm('neural_network')}
                >
                  <CardContent className="pt-6">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="p-2 bg-purple-100 rounded-lg">
                        <Activity className="h-6 w-6 text-purple-600" />
                      </div>
                      <div>
                        <h3 className="font-semibold">Neural Network</h3>
                        <p className="text-sm text-muted-foreground">Deep Learning</p>
                      </div>
                    </div>
                    <ul className="text-sm space-y-1 text-muted-foreground">
                      <li>✓ Captures complex patterns</li>
                      <li>✓ Flexible architecture</li>
                      <li>✓ State-of-the-art performance</li>
                      <li>✓ Works with any data type</li>
                    </ul>
                  </CardContent>
                </Card>
              </div>

              {/* Feature Suggestions */}
              {suggestions && (
                <Card className="bg-muted/50">
                  <CardHeader>
                    <CardTitle className="text-sm flex items-center gap-2">
                      <Sparkles className="h-4 w-4" />
                      AI Feature Engineering Suggestions
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {suggestions.polynomial_features?.length > 0 && (
                      <div>
                        <p className="text-sm font-medium mb-1">Polynomial Features:</p>
                        {suggestions.polynomial_features.slice(0, 3).map((item: any, i: number) => (
                          <p key={i} className="text-sm text-muted-foreground">
                            • {item.column}: Try {item.suggestion} transform (skew: {item.skewness.toFixed(2)})
                          </p>
                        ))}
                      </div>
                    )}
                    {suggestions.interaction_features?.length > 0 && (
                      <div>
                        <p className="text-sm font-medium mb-1">Interaction Features:</p>
                        {suggestions.interaction_features.slice(0, 3).map((item: any, i: number) => (
                          <p key={i} className="text-sm text-muted-foreground">
                            • Combine {item.col1} × {item.col2} (correlation: {item.correlation.toFixed(2)})
                          </p>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}

              <div className="flex gap-2">
                <Button variant="outline" onClick={() => setStep(1)} className="flex-1">
                  Back
                </Button>
                <Button onClick={() => setStep(3)} className="flex-1">
                  Configure Parameters
                  <ChevronRight className="ml-2 h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Step 3: Configure Parameters */}
      {step === 3 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                Step 3: Configure Parameters
              </CardTitle>
              <CardDescription>
                Fine-tune your model settings
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* General Parameters */}
              <div className="space-y-4">
                <h3 className="font-semibold">General Settings</h3>
                
                <div>
                  <Label>Test Size: {(testSize * 100).toFixed(0)}%</Label>
                  <Slider
                    value={[testSize * 100]}
                    onValueChange={([value]) => setTestSize(value / 100)}
                    min={10}
                    max={50}
                    step={5}
                    className="mt-2"
                  />
                  <p className="text-xs text-muted-foreground mt-1">
                    Train: {((1 - testSize) * 100).toFixed(0)}% | Test: {(testSize * 100).toFixed(0)}%
                  </p>
                </div>

                <div className="flex items-center justify-between">
                  <Label>Save Model</Label>
                  <Switch checked={saveModel} onCheckedChange={setSaveModel} />
                </div>
              </div>

              <Separator />

              {/* Algorithm-specific Parameters */}
              {algorithm === 'xgboost' ? (
                <div className="space-y-4">
                  <h3 className="font-semibold">XGBoost Parameters</h3>
                  
                  <div>
                    <Label>Number of Estimators: {nEstimators}</Label>
                    <Slider
                      value={[nEstimators]}
                      onValueChange={([value]) => setNEstimators(value)}
                      min={10}
                      max={500}
                      step={10}
                      className="mt-2"
                    />
                  </div>

                  <div>
                    <Label>Max Depth: {maxDepth}</Label>
                    <Slider
                      value={[maxDepth]}
                      onValueChange={([value]) => setMaxDepth(value)}
                      min={1}
                      max={20}
                      step={1}
                      className="mt-2"
                    />
                  </div>

                  <div>
                    <Label>Learning Rate: {learningRate.toFixed(3)}</Label>
                    <Slider
                      value={[learningRate * 100]}
                      onValueChange={([value]) => setLearningRate(value / 100)}
                      min={1}
                      max={100}
                      step={1}
                      className="mt-2"
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <Label>Auto-tune Hyperparameters</Label>
                      <p className="text-xs text-muted-foreground">
                        Automatically find best parameters (slower)
                      </p>
                    </div>
                    <Switch 
                      checked={tuneHyperparameters} 
                      onCheckedChange={setTuneHyperparameters} 
                    />
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  <h3 className="font-semibold">Neural Network Parameters</h3>
                  
                  <div>
                    <Label>Hidden Layers (comma-separated)</Label>
                    <Input
                      value={hiddenLayers}
                      onChange={(e) => setHiddenLayers(e.target.value)}
                      placeholder="64,32"
                    />
                    <p className="text-xs text-muted-foreground mt-1">
                      Example: 64,32 = 2 layers with 64 and 32 neurons
                    </p>
                  </div>

                  <div>
                    <Label>Dropout Rate: {dropoutRate.toFixed(2)}</Label>
                    <Slider
                      value={[dropoutRate * 100]}
                      onValueChange={([value]) => setDropoutRate(value / 100)}
                      min={0}
                      max={50}
                      step={5}
                      className="mt-2"
                    />
                  </div>

                  <div>
                    <Label>Epochs: {epochs}</Label>
                    <Slider
                      value={[epochs]}
                      onValueChange={([value]) => setEpochs(value)}
                      min={10}
                      max={200}
                      step={10}
                      className="mt-2"
                    />
                  </div>

                  <div>
                    <Label>Batch Size: {batchSize}</Label>
                    <Slider
                      value={[batchSize]}
                      onValueChange={([value]) => setBatchSize(value)}
                      min={8}
                      max={256}
                      step={8}
                      className="mt-2"
                    />
                  </div>
                </div>
              )}

              <div className="flex gap-2">
                <Button variant="outline" onClick={() => setStep(2)} className="flex-1">
                  Back
                </Button>
                <Button 
                  onClick={handleTrain} 
                  className="flex-1"
                  disabled={training}
                >
                  {training ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Training Model...
                    </>
                  ) : (
                    <>
                      <Zap className="mr-2 h-4 w-4" />
                      Train Model
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Step 4: Results */}
      {step === 4 && result && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                Training Complete!
              </CardTitle>
              <CardDescription>
                Your {algorithm === 'xgboost' ? 'XGBoost' : 'Neural Network'} model has been trained successfully
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Metrics */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(result.metrics || {}).map(([key, value]: [string, any]) => (
                  <div key={key} className="p-4 border rounded-lg">
                    <p className="text-sm text-muted-foreground capitalize">
                      {key.replace(/_/g, ' ')}
                    </p>
                    <p className={`text-2xl font-bold ${getMetricColor(value, key)}`}>
                      {typeof value === 'number' ? value.toFixed(4) : JSON.stringify(value)}
                    </p>
                  </div>
                ))}
              </div>

              {/* Feature Importance */}
              {result.feature_importance && result.feature_importance.length > 0 && (
                <div>
                  <h3 className="font-semibold mb-3">Top Feature Importance</h3>
                  <div className="space-y-2">
                    {result.feature_importance.slice(0, 10).map((item: any, i: number) => (
                      <div key={i} className="flex items-center gap-3">
                        <span className="text-sm font-medium w-32 truncate">{item.feature}</span>
                        <div className="flex-1 bg-muted rounded-full h-2 overflow-hidden">
                          <div 
                            className="bg-primary h-full"
                            style={{ width: `${(item.importance / result.feature_importance[0].importance) * 100}%` }}
                          />
                        </div>
                        <span className="text-sm text-muted-foreground w-16 text-right">
                          {item.importance.toFixed(4)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Training History for NN */}
              {result.training_history && (
                <div>
                  <h3 className="font-semibold mb-3">Training Progress</h3>
                  <div className="h-48 flex items-end gap-1">
                    {result.training_history.loss.map((loss: number, i: number) => {
                      const maxLoss = Math.max(...result.training_history.loss)
                      const height = (loss / maxLoss) * 100
                      return (
                        <div
                          key={i}
                          className="flex-1 bg-red-500/20 hover:bg-red-500/40 transition-colors"
                          style={{ height: `${height}%` }}
                          title={`Epoch ${i + 1}: Loss ${loss.toFixed(4)}`}
                        />
                      )
                    })}
                  </div>
                  <p className="text-xs text-muted-foreground text-center mt-2">
                    Training Loss over {result.epochs_trained} epochs
                  </p>
                </div>
              )}

              <div className="flex gap-2">
                <Button variant="outline" onClick={() => {
                  setStep(1)
                  setResult(null)
                }} className="flex-1">
                  Train Another Model
                </Button>
                <Button className="flex-1" onClick={() => window.location.href = '/history'}>
                  View in History
                  <Star className="ml-2 h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}
    </div>
  )
}
