import React from "react";
import Button from "@material-ui/core/Button";
import SendIcon from "@material-ui/icons/Send";
import ReplayIcon from "@material-ui/icons/Replay";
import Paper from "@material-ui/core/Paper";
import InputLabel from "@material-ui/core/InputLabel";
import MenuItem from "@material-ui/core/MenuItem";
import FormControl from "@material-ui/core/FormControl";
import Select from "@material-ui/core/Select";
import TextField from "@material-ui/core/TextField";
import Typography from "@material-ui/core/Typography";

import Portfolio from "./Portfolio";

class Search extends React.Component {
    REACT_APP_URL = "http://localhost:4800/";

    componentDidMount() {
        this.getParameters();
        this.getEtfsMatchingFilters();
    }

    initialOptimizerParameters = {
        optimizer: "MaxSharpe",
        targetVolatility: 0.1,
        targetReturn: 0.1,
        assetCutoff: 0.01,
        assetRounding: 4,
        riskFreeRate: 0.02,
        shorting: false,
        removeTER: true,
        rollingWindowInDays: 0,
        maxETFListSize: 400,
    };

    initialETFFilters = {
        minimumDaysWithData: 4000,
    };

    state = {
        parameters: {},
        etfsMatchingFilters: 0,
        totalETFs: 0,
        optimizerParameters: this.initialOptimizerParameters,
        etfFilters: this.initialETFFilters,
        optimizedResponse: null,
        loadingResponse: false,
        error: null,
    };

    render() {
        const { optimizerParameters, etfsMatchingFilters, totalETFs, etfFilters, parameters, optimizedResponse, loading, error } =
            this.state;

        return (
            <React.Fragment>
                <Paper
                    elevation={10}
                    variant="outlined"
                    style={{
                        backgroundColor: "darkgray",
                        marginLeft: "100px",
                        marginRight: "100px",
                    }}
                >
                    <Paper
                        elevation={10}
                        variant="outlined"
                        style={{
                            backgroundColor: "lightGray",
                            marginLeft: "20px",
                            marginRight: "20px",
                            marginTop: "10px",
                        }}
                    >
                        <Typography variant="body2" style={{ margin: "10px", fontWeight: "bold" }}>
                            Optimizer Parameters
                        </Typography>
                        <div className="optimizerParameters" style={{ flexDirection: "row", margin: "5px" }}>
                            <FormControl style={{ margin: "5px" }}>
                                <InputLabel id="optimizer">Optimizer</InputLabel>
                                <Select
                                    labelId="optimizer"
                                    id="optimizer-select"
                                    value={
                                        parameters.optimizers && optimizerParameters.optimizer != null ? optimizerParameters.optimizer : ""
                                    }
                                    onChange={(e) => this.handleChangeOptimizerParameter(e.target.value, "optimizer")}
                                >
                                    {parameters.optimizers &&
                                        parameters.optimizers.map((option, index) => (
                                            <MenuItem key={option} value={option}>
                                                {option}
                                            </MenuItem>
                                        ))}
                                </Select>
                            </FormControl>
                            {optimizerParameters.optimizer === "EfficientRisk" && (
                                <TextField
                                    id="targetVolatility"
                                    label="Target Volatility"
                                    type="number"
                                    value={optimizerParameters.targetVolatility != null ? optimizerParameters.targetVolatility : ""}
                                    style={{ margin: "5px", width: "115px" }}
                                    onChange={(e) => this.handleChangeOptimizerParameter(e.target.value, "targetVolatility")}
                                />
                            )}
                            {optimizerParameters.optimizer === "EfficientReturn" && (
                                <TextField
                                    id="targetReturn"
                                    label="Target Return"
                                    type="number"
                                    value={optimizerParameters.targetReturn != null ? optimizerParameters.targetReturn : ""}
                                    style={{ margin: "5px", width: "100px" }}
                                    onChange={(e) => this.handleChangeOptimizerParameter(e.target.value, "targetReturn")}
                                />
                            )}
                            <TextField
                                id="assetCutoff"
                                label="Asset Cutoff"
                                type="number"
                                value={optimizerParameters.assetCutoff != null ? optimizerParameters.assetCutoff : ""}
                                style={{ margin: "5px", width: "100px" }}
                                onChange={(e) => this.handleChangeOptimizerParameter(parseFloat(e.target.value), "assetCutoff")}
                            />
                            <TextField
                                id="assetRounding"
                                label="Asset Rounding"
                                type="number"
                                value={optimizerParameters.assetRounding != null ? optimizerParameters.assetRounding : ""}
                                style={{ margin: "5px", width: "120px" }}
                                onChange={(e) => this.handleChangeOptimizerParameter(parseInt(e.target.value), "assetRounding")}
                            />
                            <TextField
                                id="riskFreeRate"
                                label="Risk free Rate"
                                type="number"
                                value={optimizerParameters.riskFreeRate != null ? optimizerParameters.riskFreeRate : ""}
                                style={{ margin: "5px", width: "110px" }}
                                onChange={(e) => this.handleChangeOptimizerParameter(parseFloat(e.target.value), "riskFreeRate")}
                            />
                            <TextField
                                id="rollingWindowInDays"
                                label="Rolling window in days"
                                type="number"
                                value={optimizerParameters.rollingWindowInDays != null ? optimizerParameters.rollingWindowInDays : ""}
                                style={{ margin: "5px", width: "175px" }}
                                onChange={(e) => this.handleChangeOptimizerParameter(parseInt(e.target.value), "rollingWindowInDays")}
                            />
                            <TextField
                                id="maxETFListSize"
                                label="Max ETF list size"
                                type="number"
                                value={optimizerParameters.maxETFListSize != null ? optimizerParameters.maxETFListSize : ""}
                                style={{ margin: "5px", width: "125px" }}
                                onChange={(e) => this.handleChangeOptimizerParameter(parseInt(e.target.value), "maxETFListSize")}
                            />
                        </div>
                    </Paper>

                    <Paper
                        elevation={10}
                        variant="outlined"
                        style={{
                            backgroundColor: "lightGray",
                            marginLeft: "20px",
                            marginRight: "20px",
                            marginTop: "10px",
                        }}
                    >
                        <Typography variant="body2" style={{ margin: "10px", fontWeight: "bold" }}>
                            ETF Filters
                        </Typography>
                        <div className="etfFilters" style={{ flexDirection: "row", margin: "5px" }}>
                            <TextField
                                id="minimumDaysWithData"
                                label="Minimum days with data"
                                type="number"
                                value={etfFilters.minimumDaysWithData != null ? etfFilters.minimumDaysWithData : ""}
                                style={{ margin: "5px", width: "200px" }}
                                onChange={(e) => this.handleChangeETFFilters(parseInt(e.target.value), "minimumDaysWithData")}
                            />
                            <FormControl style={{ margin: "5px" }}>
                                <InputLabel id="domicileCountry">Domicile Country</InputLabel>
                                <Select
                                    labelId="domicileCountry"
                                    id="domicileCountry-select"
                                    value={
                                        parameters.domicileCountries && etfFilters.domicileCountry != null ? etfFilters.domicileCountry : ""
                                    }
                                    style={{ minWidth: "150px" }}
                                    onClick={(e) =>
                                        this.handleChangeETFFilters(e.target.value === 0 ? null : e.target.value, "domicileCountry")
                                    }
                                >
                                    {parameters.domicileCountries &&
                                        parameters.domicileCountries.map((option, index) => (
                                            <MenuItem key={option} value={option}>
                                                {option}
                                            </MenuItem>
                                        ))}
                                </Select>
                            </FormControl>
                            <FormControl style={{ margin: "5px" }}>
                                <InputLabel id="replicationMethod">Replication Method</InputLabel>
                                <Select
                                    labelId="replicationMethod"
                                    id="replicationMethod-select"
                                    value={
                                        parameters.replicationMethods && etfFilters.replicationMethod != null
                                            ? etfFilters.replicationMethod
                                            : ""
                                    }
                                    style={{ minWidth: "175px" }}
                                    onClick={(e) =>
                                        this.handleChangeETFFilters(e.target.value === 0 ? null : e.target.value, "replicationMethod")
                                    }
                                >
                                    {parameters.replicationMethods &&
                                        parameters.replicationMethods.map((option, index) => (
                                            <MenuItem key={option} value={option}>
                                                {option}
                                            </MenuItem>
                                        ))}
                                </Select>
                            </FormControl>
                            <FormControl style={{ margin: "5px" }}>
                                <InputLabel id="distributionPolicy">Distribution Policy</InputLabel>
                                <Select
                                    labelId="distributionPolicy"
                                    id="distributionPolicy-select"
                                    value={
                                        parameters.distributionPolicies && etfFilters.distributionPolicy != null
                                            ? etfFilters.distributionPolicy
                                            : ""
                                    }
                                    style={{ minWidth: "175px" }}
                                    onClick={(e) =>
                                        this.handleChangeETFFilters(e.target.value === 0 ? null : e.target.value, "distributionPolicy")
                                    }
                                >
                                    {parameters.distributionPolicies &&
                                        parameters.distributionPolicies.map((option, index) => (
                                            <MenuItem key={option} value={option}>
                                                {option}
                                            </MenuItem>
                                        ))}
                                </Select>
                            </FormControl>
                        </div>
                    </Paper>
                    <Typography variant="body1" component="h2" style={{ margin: "10px" }}>
                        {"ETFs matching filters: " + etfsMatchingFilters + " out of " + totalETFs}
                    </Typography>

                    <div className="buttons" style={{ flexDirection: "row", margin: "10px" }}>
                        <Button variant="contained" color="primary" endIcon={<SendIcon />} onClick={this.callOptimizer}>
                            Optimize
                        </Button>
                        <Button variant="contained" endIcon={<ReplayIcon />} style={{ float: "right" }} onClick={this.resetFilters}>
                            Reset Filters
                        </Button>
                    </div>
                </Paper>

                {(loading || optimizedResponse != null || error != null) && (
                    <Paper
                        elevation={10}
                        variant="outlined"
                        style={{
                            backgroundColor: "darkgray",
                            marginLeft: "100px",
                            marginRight: "100px",
                            marginTop: "25px",
                            marginBottom: "50px",
                            paddingLeft: "10px",
                        }}
                    >
                        <Portfolio
                            portfolio={optimizedResponse}
                            loading={loading}
                            error={error}
                            onCloseError={(e) => this.setState({ error: null, optimizedResponse: null })}
                            assetRounding={optimizerParameters.assetRounding}
                        />
                    </Paper>
                )}
            </React.Fragment>
        );
    }

    handleChangeOptimizerParameter = (value, parameterName) => {
        const { optimizerParameters } = this.state;
        let newOptimizerParameters = { ...optimizerParameters };

        if (value == null || Number.isNaN(value)) {
            delete newOptimizerParameters[parameterName];
        } else {
            newOptimizerParameters[parameterName] = value;
        }

        this.setState({ optimizerParameters: newOptimizerParameters });
    };

    handleChangeETFFilters = (value, filterName) => {
        const { etfFilters } = this.state;
        let newETFFilters = { ...etfFilters };

        if (value == null || Number.isNaN(value)) {
            delete newETFFilters[filterName];
        } else {
            newETFFilters[filterName] = value;
        }

        this.setState({ etfFilters: newETFFilters }, this.getEtfsMatchingFilters);
    };

    resetFilters = () => {
        this.setState(
            {
                optimizerParameters: this.initialOptimizerParameters,
                etfFilters: this.initialETFFilters,
            },
            this.getEtfsMatchingFilters
        );
    };

    getParameters = () => {
        fetch(this.REACT_APP_URL + "parameters")
            .then(async (response) => {
                const data = await response.json();
                // check for error response
                if (!response.ok) {
                    // get error message from body or default to response statusText
                    const error = (data && data.error) || response.statusText;
                    return Promise.reject(error);
                }

                this.setState({ parameters: data });
            })
            .catch((error) => {
                console.error("There was an error getting the parameters for the ETFs!", error);
            });
    };

    getEtfsMatchingFilters = () => {
        const { etfFilters } = this.state;
        fetch(this.REACT_APP_URL + "etfsMatchingFilters", {
            headers: {
                Accept: "application/json",
                "Content-Type": "application/json",
            },
            method: "POST",
            body: JSON.stringify({
                etfFilters: etfFilters,
            }),
        })
            .then(async (response) => {
                const data = await response.json();
                // check for error response
                if (!response.ok) {
                    // get error message from body or default to response statusText
                    const error = (data && data.error) || response.statusText;
                    return Promise.reject(error);
                }

                this.setState({ etfsMatchingFilters: data.etfsMatchingFilters, totalETFs: data.totalETFs });
            })
            .catch((error) => {
                console.error("There was an error getting the ETFs that match the filters!", error);
            });
    };

    callOptimizer = () => {
        const { optimizerParameters, etfFilters } = this.state;

        this.setState({ optimizedResponse: null, loading: true, error: null });

        fetch(this.REACT_APP_URL + "optimize", {
            headers: {
                Accept: "application/json",
                "Content-Type": "application/json",
            },
            method: "POST",
            body: JSON.stringify({
                optimizerParameters: optimizerParameters,
                etfFilters: etfFilters,
            }),
        })
            .then(async (response) => {
                const data = await response.json();
                // check for error response
                if (!response.ok) {
                    // get error message from body or default to response statusText
                    const error = (data && data.error) || response.statusText;
                    return Promise.reject(error);
                }

                this.setState({ optimizedResponse: data, loading: false });
            })
            .catch((error) => {
                if (typeof error === "object") {
                    this.setState({ loading: false, error: error.message });
                } else {
                    this.setState({ loading: false, error: error });
                }
                console.error("There was an error getting the optimzed portfolio!", error);
            });
    };
}

export default Search;
