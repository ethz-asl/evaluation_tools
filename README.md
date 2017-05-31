# Evaluation Tools

# 1. Introduction
This package provides an automatic evaluation framework for Maplab. It allows users to run a ROS executable, such as `swe_app` over different datasets and different parameter configurations, and provides an interface to evaluate the run through scripts.

A simple standard evaluation script is provided, which collects and plots statistics from the runs. For more detailed and specific analysis, there is room for the users to create their own evaluation scripts.


#### 1.1 Experiments
The evaluation tools framework fundamental testing units are called experiments. Whenever a user wants to perform an evaluation, the first step is to create an experiment yaml file, specifying some characteristics of the tasks he or she wants to be run. A sample experiment that can be used as a starting point can be found in `experiments/sample_experiment.yaml` 

Experiments files will tell the framework which configuration, datasets and parameter files should be used with the excutable the user wants to run. For each pair of (parameter_file, dataset), a different job will be created and ran. For example, if there are 5 parameter files and 2 datasets, a total of 10 runs will take place.

#### 1.2 Parameter files and parameter sweep
Each parameter file include parameters that will be passed to the executable in the corresponding run. As an example, see `parameter_files/sample_parameters_1.yaml`.

Additionally, one can define one __parameter sweep__ inside the parameter file. A parameter sweep allows the user to test different values of a same parameter without needing to create many different parameter files. Parameter sweeps can be very powerful. As an example of how to use one, please see `parameter_files/sample_parameters_with_sweep.yaml`

A parameter file containing a parameter sweep will be transformed into as many parameter files as the number of values that the parameter will take, affecting the number of runs. For example, if an experiment includes 2 parameter files with no sweep, a parameter file with a sweep that takes 10 values, and 3 datasets, the total number of runs will be (2 + 10) * 3 = 26 runs.

#### 1.3 Evaluating runs and Simple summarization
An important part of the evaluation tools framework is to allow the user to perform evaluation of the runs. The simplest way to do so is to use the __Simple summarization__ feature of the evaluation tools framework.

If the simple summarization is enabled, all statistics defined in the runs will be analyzed and plotted nicely. It is very simple to add extra statistics that we are interested in. One just has to add an instance of the StatsCollector class found inside `maplab/common/statistics` to capture the interesting metrics, and add samples when convenient.

There are many examples on how to use these statistics around the codebase (like here, or here), but let's create our own example to make it even clearer.

Let's suppose that we want to evaluate how different parameters affect how big a reprojection error gets. For convenience, let's assume that there is a function called `computeReprojectionError()` that returns a float.

Then, somewhere in the code, we would already have:
```cpp
double reprojection_error = computeReprojectionError();
```

In order to add this as a statistics, one would simply enclose the previous code with the following:
```cpp
statistics::StatsCollector stat_repr_error("reprojection_error");
double reprojection_error = computeReprojectionError();
stat_repr_error.AddSample(reprojection_error);
```

With this simple change, now the evaluation framework can capture and plot the evolution of the reprojection_error metric with respect to the different parameters used.

In order to use Simple summarization, the experiment yaml file should include the summarize_statistics field. See `experiments/sample_experiment.yaml` for an example, that also includes the extra options that can be specified : white/blacklisting metrics, or grouping plots of parameter sweeps.

Note: The simple summarization is only supported when using the `swe_app` executable.

# 2. Usage
### 2.1 Forming an experiment file
Now that we know how the evaluation tools framework works, let's explain how to use it. The first step is to form an experiment file. The best idea is to start from the `experiments/sample_experiment.yaml` and adapt it to create the desired experiment. Here is a detailed list of the different fields:

##### Necessary fields
An experiments yaml file must contain the following fields:

* __experiment_name__: Name the user wants to give to the current experiment. It can be anything.
* __app_package_name__: Package of the executable (what comes after rosrun in `rosrun pkg exec`)
* __app_executable__: Actual executable (what comes last in `rosrun pkg exec`)
* __ncamera_calibration_file__: Path to the vehicle ncamera calibration file.
* __wheel_odometry_calibration_file__: Path to the vehicle wheel odometry calibration file.
* __parameter_files__: Which parameter files will be used in the experiment.
* __datasets__: Which datasets will be used in the experiment.

##### Optional fields
* __global_parameters__: Parameters defined here will be used for all experiments and overwrite those inside the parameter files. This is useful to specify parameters that are the same in every experiment and are of no interest to the evaluation.
* __preprocessing_scripts[Advanced]__: Any script that is listed here will be run before each job.
* __evaluation_scripts[Advanced]__: Any script that is listed here will be run after each job.
* __summarize_statistics__: Enable and configure simple summarization.

### 2.2 Running the experiment
Once the experiments yaml file is created, the user has to run the `python/run_experiment.py` script, specifying which experiment file to use as an argument, as in:
```bash
roscd evaluation_tools
python/run_experiment.py sample_experiment.yaml
```
